"""Investigation workflow orchestration (Phase 1 + 3 of PLAN.md).

Ported from the original demonstrator's ``application_workflow.py``. The pipeline
is deterministic, so each mechanical step is a code node rather than a tool call
the model could skip or fabricate. Application agents (typed PydanticAI agents)
are used only to interpret intent and summarize findings. Human gates are
``interrupt()`` points, resumable via the PostgreSQL-backed checkpointer.

Differences from the original, per the target architecture:
- All data access goes through ``mcp_capability_adaptor.client`` (MCP tools),
  never a direct platform client import.
- Model calls go through ``agent_runtime.application_agent.agents`` (typed
  PydanticAI agents), not a raw ``with_structured_output`` call.
- Checkpointing uses ``foundation.postgres_checkpointer`` (PostgreSQL), not SQLite.
- Session/audit events use ``foundation.session_manager`` (PostgreSQL), not SQLite.
"""

import logging
import re
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from agent_runtime.application_agent.agents import parse_scope as agent_parse_scope
from agent_runtime.application_agent.agents import summarize_findings
from agent_runtime.application_agent.contracts import (
    DEFAULT_BASELINE_DEVIATION_PCT,
    DEFAULT_LIMIT_VALUE,
)
from application_ui.opo_monitoring_service import services
from foundation import session_manager
from foundation.postgres_checkpointer import build_checkpointer

log = logging.getLogger(__name__)

MAX_REGISTRATION_POLLS = 10
MIN_LIMIT_VALUE = 0.0


def _keep_last(_current: Any, incoming: Any) -> Any:
    return incoming


class InvestigationState(TypedDict, total=False):
    question: str
    mode: str
    limit_value: float
    requested_limit_value: float
    direction: str
    threshold_unit: str
    baseline_deviation_pct: float
    interpretation: str
    lookback_days: int
    machine_id: str | None
    lot_id: str | None
    product_id: str | None
    layer_id: str | None
    exposure_equipment_id: str | None
    threshold_context: dict
    threshold_recommendation: dict
    needs_threshold_clarification: bool
    trend_series: list[dict]
    analysis: Annotated[list[dict], _keep_last]
    outliers: Annotated[list[dict], _keep_last]
    selected: dict
    workspace_id: str
    filters: dict
    registration: dict
    registration_history: Annotated[list[dict], _keep_last]
    wafer_data: dict
    findings: dict
    cancelled_at: str


def _is_approved(decision: Any) -> bool:
    if isinstance(decision, dict):
        return bool(decision.get("approved", True))
    if isinstance(decision, str):
        return decision.strip().lower() in {"y", "yes", "approve", "approved", "true"}
    return bool(decision)


def parse_scope(state: InvestigationState) -> InvestigationState:
    """Choose the detection rule from the analyst's phrasing; detection itself stays in code.

    Does not itself call ``interrupt()``: LangGraph re-executes a node's entire function
    body (including any LLM calls) from the top every time that node resumes from an
    interrupt, so the interrupt for an absolute-threshold clarification lives in the
    separate, minimal ``confirm_absolute_threshold`` node below instead.
    """
    question = state.get("question", "")
    mode = "baseline"
    limit = DEFAULT_LIMIT_VALUE
    direction = "below"
    threshold_unit = "percent"
    deviation = DEFAULT_BASELINE_DEVIATION_PCT
    interpretation = (
        f"No limit named, so each machine is compared against its own median "
        f"({DEFAULT_BASELINE_DEVIATION_PCT}% increase counts as abnormal)."
    )
    lookback_days = 14
    machine_id = None
    lot_id = None
    product_id = None
    layer_id = None
    exposure_equipment_id = None

    threshold_context: dict[str, Any] = {}
    threshold_recommendation: dict[str, Any] = {}
    suggested_limit_value: float | None = None
    suggested_limit_rationale: str | None = None
    # Empirical context for a *default* (unfiltered, 14-day) lookback, computed up front
    # with no LLM call so the single model call below can recommend a cutoff in the same
    # response instead of needing a second round-trip once filters are known.
    default_threshold_context = services.get_kpi_threshold_context(days=14)
    try:
        with session_manager.timed_event("model_call", {"purpose": "scope_interpretation"}):
            scope = agent_parse_scope(question, default_threshold_context)
        mode = scope.mode
        limit = float(scope.limit_value)
        direction = scope.direction
        threshold_unit = scope.threshold_unit
        deviation = float(scope.baseline_deviation_pct or DEFAULT_BASELINE_DEVIATION_PCT)
        interpretation = scope.interpretation
        lookback_days = scope.lookback_days
        machine_id = scope.machine_id
        lot_id = scope.lot_id
        product_id = scope.product_id
        layer_id = scope.layer_id
        exposure_equipment_id = scope.exposure_equipment_id
        suggested_limit_value = scope.suggested_limit_value
        suggested_limit_rationale = scope.suggested_limit_rationale
        session_manager.record_event(
            "model_interpretation",
            {"request": question, "interpretation": scope.model_dump()},
            source="application",
        )
    except Exception:
        log.warning("Could not parse scope from %r; using default", question, exc_info=True)
        session_manager.record_event(
            "model_interpretation",
            {"request": question, "interpretation": "fallback_defaults", "fallback": True},
            source="application",
        )

    threshold_match = re.search(
        r"\b(above|below|over|under|greater than|less than|more than|at least)\s+"
        r"(\d+(?:\.\d+)?)\s*(%)?",
        question,
        re.IGNORECASE,
    )
    if threshold_match:
        mode = "absolute"
        direction = "below" if threshold_match.group(1).lower() in {"below", "under", "less than"} else "above"
        limit = float(threshold_match.group(2))
        threshold_unit = "percent" if threshold_match.group(3) or "%" in question else "absolute"

    lookback_days = min(max(int(lookback_days), 1), 90)

    if not threshold_match:
        threshold_context = services.get_kpi_threshold_context(
            days=lookback_days,
            machine_id=machine_id,
            lot_id=lot_id,
            product_id=product_id,
            layer_id=layer_id,
            exposure_equipment_id=exposure_equipment_id,
        )
        if suggested_limit_value is not None:
            suggested_limit = float(suggested_limit_value)
            threshold_recommendation = {
                "suggested_limit_value": suggested_limit,
                "rationale": suggested_limit_rationale or "Suggested from the empirical P95/P99 OPO KPI distribution.",
            }
        else:
            log.warning("Model did not recommend a KPI threshold for %r; using empirical fallback", question)
            suggested_limit = float(threshold_context.get("p95") or threshold_context.get("p99") or DEFAULT_LIMIT_VALUE)
            threshold_recommendation = {
                "suggested_limit_value": suggested_limit,
                "rationale": "Suggested from the empirical P95/P99 OPO KPI distribution.",
            }
        session_manager.record_event(
            "threshold_recommendation",
            {"context": threshold_context, "recommendation": threshold_recommendation},
            source="application",
        )
        return {
            "mode": mode,
            "direction": direction,
            "threshold_unit": threshold_unit,
            "baseline_deviation_pct": deviation,
            "interpretation": interpretation,
            "lookback_days": lookback_days,
            "machine_id": machine_id,
            "lot_id": lot_id,
            "product_id": product_id,
            "layer_id": layer_id,
            "exposure_equipment_id": exposure_equipment_id,
            "threshold_context": threshold_context,
            "threshold_recommendation": threshold_recommendation,
            "needs_threshold_clarification": True,
        }

    # Clamped only at the bounds of physical meaning, and the original is kept so the
    # UI can say when it differed rather than silently answering a different question
    # Unitless thresholds refer to the absolute OPO KPI scale (roughly 2.8-3.3).
    if mode == "absolute" and "%" not in question:
        threshold_unit = "absolute"
    effective = max(limit, MIN_LIMIT_VALUE)
    return {
        "mode": mode,
        "limit_value": effective,
        "requested_limit_value": limit,
        "direction": direction,
        "threshold_unit": threshold_unit,
        "baseline_deviation_pct": deviation,
        "interpretation": interpretation,
        "lookback_days": lookback_days,
        "machine_id": machine_id,
        "lot_id": lot_id,
        "product_id": product_id,
        "layer_id": layer_id,
        "exposure_equipment_id": exposure_equipment_id,
        "threshold_context": threshold_context,
        "threshold_recommendation": threshold_recommendation,
        "needs_threshold_clarification": False,
    }


def confirm_absolute_threshold(state: InvestigationState) -> InvestigationState:
    """Ask the analyst to accept or edit the recommended absolute KPI cutoff.

    Kept minimal - the interrupt is the first real statement - because LangGraph
    re-executes a node's whole function body from the top on every resume from an
    interrupt; if the LLM call from ``parse_scope`` lived here too, accepting the
    threshold would re-run that model call (and its latency) again.
    """
    threshold_context = state.get("threshold_context") or {}
    threshold_recommendation = state.get("threshold_recommendation") or {}
    suggested_limit = threshold_recommendation.get("suggested_limit_value", DEFAULT_LIMIT_VALUE)
    clarification = interrupt(
        {
            "type": "clarify_absolute_threshold",
            "question": "Which absolute OPO KPI threshold should count as an outlier?",
            "metric": "OPO KPI",
            "unit": "absolute",
            "default_not_applied": True,
            "p95": threshold_context.get("p95"),
            "p99": threshold_context.get("p99"),
            "suggested_limit_value": suggested_limit,
            "rationale": threshold_recommendation.get("rationale"),
        }
    )
    if not _is_approved(clarification):
        return {"cancelled_at": "clarify_absolute_threshold"}
    if isinstance(clarification, dict):
        limit = float(clarification.get("limit_value", suggested_limit))
    else:
        limit = float(clarification)
    limit = max(limit, MIN_LIMIT_VALUE)
    return {
        "mode": "absolute",
        "limit_value": limit,
        "requested_limit_value": limit,
        "direction": "above",
        "threshold_unit": "absolute",
        "interpretation": f"Absolute OPO KPI values at or above {limit} will be treated as outliers.",
    }


def analyze_trends(state: InvestigationState) -> InvestigationState:
    analysis = services.analyse_series(
        mode=state.get("mode", "baseline"),
        limit_value=state.get("limit_value", DEFAULT_LIMIT_VALUE),
        direction=state.get("direction", "below"),
        limit_unit=state.get("threshold_unit", "percent"),
        baseline_deviation_pct=state.get("baseline_deviation_pct", DEFAULT_BASELINE_DEVIATION_PCT),
        days=state.get("lookback_days", 14),
        machine_id=state.get("machine_id"),
        lot_id=state.get("lot_id"),
        product_id=state.get("product_id"),
        layer_id=state.get("layer_id"),
        exposure_equipment_id=state.get("exposure_equipment_id"),
    )
    trend_series = services.get_trend_series(
        days=state.get("lookback_days", 14),
        machine_id=state.get("machine_id"),
        lot_id=state.get("lot_id"),
        product_id=state.get("product_id"),
        layer_id=state.get("layer_id"),
        exposure_equipment_id=state.get("exposure_equipment_id"),
    )
    outliers = sorted(
        (a for a in analysis if a["outlier_dates"]),
        key=lambda a: a["deviation_pct"],
        reverse=True,
    )
    if not outliers:
        return {"analysis": analysis, "outliers": outliers, "trend_series": trend_series}

    # Fetch the point-level StarRocks preview as soon as trend outliers are known,
    # so the first response can render the wafer map before approval continues.
    wafer_table = services.get_dataset_metadata()["wafer_table"]
    wafer_filters = {
        "machine": state.get("machine_id") or state.get("exposure_equipment_id") or outliers[0]["machine"],
        "layer_id": state.get("layer_id"),
    }
    if state.get("lot_id"):
        wafer_filters["lot_id"] = state["lot_id"]
    elif outliers[0].get("outlier_lot_ids"):
        wafer_filters["lot_ids"] = outliers[0]["outlier_lot_ids"]
    wafer_data = services.query_wafer_data("TREND_PREVIEW", wafer_table, wafer_filters)
    return {"analysis": analysis, "outliers": outliers, "trend_series": trend_series, "wafer_data": wafer_data}


def confirm_investigation(state: InvestigationState) -> InvestigationState:
    candidate = state["outliers"][0]
    decision = interrupt(
        {
            "type": "confirm_investigation",
            "question": "Investigate the most extreme outlier?",
            "candidate": candidate,
            "all_outliers": state["outliers"],
            "mode": state.get("mode"),
            "limit_value": state.get("limit_value"),
            "direction": state.get("direction"),
            "threshold_unit": state.get("threshold_unit"),
        }
    )
    if not _is_approved(decision):
        return {"cancelled_at": "confirm_investigation"}

    chosen = candidate
    if isinstance(decision, dict) and decision.get("machine"):
        chosen = next(
            (o for o in state["outliers"] if o["machine"] == decision["machine"]),
            candidate,
        )
    return {"selected": chosen}


def create_workspace(state: InvestigationState) -> InvestigationState:
    return {"workspace_id": services.create_workspace()}


def apply_filters(state: InvestigationState) -> InvestigationState:
    selected = state["selected"]
    filters = {"machine": selected["machine"], "product": selected["product"]}
    if selected.get("extreme_lot_id"):
        filters["lot_id"] = selected["extreme_lot_id"]
    services.add_filters(state["workspace_id"], filters)
    return {"filters": filters}


def approve_registration(state: InvestigationState) -> InvestigationState:
    decision = interrupt(
        {
            "type": "approve_registration",
            "question": "Approve dataset registration? This provisions compute upstream.",
            "workspace_id": state["workspace_id"],
            "dataset": "overlay_wafer_points",
            "filters": state["filters"],
        }
    )
    if not _is_approved(decision):
        return {"cancelled_at": "approve_registration"}
    return {}


def register_and_wait(state: InvestigationState) -> InvestigationState:
    workspace_id = state["workspace_id"]
    history: list[dict] = []

    for _ in range(MAX_REGISTRATION_POLLS):
        status = services.register(workspace_id, "overlay_wafer_points", "overlay_wafer_points", approved=True)
        history.append(status)
        if status["status"] == "READY":
            return {"registration": status, "registration_history": history}

    raise TimeoutError(
        f"Registration for {workspace_id} did not reach READY within {MAX_REGISTRATION_POLLS} polls"
    )


def query_wafers(state: InvestigationState) -> InvestigationState:
    return {
        "wafer_data": services.query_wafer_data(
            state["workspace_id"], state["registration"]["table"], state.get("filters")
        )
    }


def summarise(state: InvestigationState) -> InvestigationState:
    wafer_data = state["wafer_data"]
    rows = wafer_data.get("rows", [])
    anomalous_wafers = wafer_data.get("anomalous_wafers", [])
    magnitudes = [r["overlay_magnitude_um"] for r in rows if r.get("overlay_magnitude_um") is not None]
    wafer_summary = {
        "row_count": len(rows),
        "anomalous_wafer_count": len(anomalous_wafers),
        "overlay_magnitude_min": round(min(magnitudes), 4) if magnitudes else None,
        "overlay_magnitude_max": round(max(magnitudes), 4) if magnitudes else None,
        "overlay_magnitude_mean": round(sum(magnitudes) / len(magnitudes), 4) if magnitudes else None,
    }
    sample_rows = [
        {k: r.get(k) for k in ("wafer_id", "lot_id", "overlay_x_um", "overlay_y_um", "overlay_magnitude_um")}
        for r in rows[:10]
    ]
    prompt = (
        "Return a structured summary with finding, evidence_references, confidence, limitations, "
        "recommended_next_actions, and alternative_explanations.\n"
        "Use only the values given below. Evidence references must use these labels: "
        "selected_outlier, applied_filters, workspace, registration, anomalous_wafers, wafer_rows. "
        "Do not invent identifiers, causes, or time ranges. If evidence is insufficient, say so.\n\n"
        f"Outlier: {state['selected']}\n"
        f"Filters applied: {state['filters']}\n"
        f"Workspace: {state['workspace_id']}\n"
        f"Registration: {state['registration']}\n"
        f"Wafer summary: {wafer_summary}\n"
        f"Sample wafer rows (first {len(sample_rows)} of {len(rows)}): {sample_rows}\n"
        f"Anomalous wafers: {anomalous_wafers}\n"
    )
    try:
        with session_manager.timed_event("model_call", {"purpose": "findings_summary"}):
            findings = summarize_findings(prompt)
        return {"findings": findings.model_dump()}
    except Exception:
        # A transient model-gateway error here shouldn't 500 the whole request and
        # strand the investigation - fall back to a plain, evidence-only summary.
        log.warning("Could not generate a findings summary; the model gateway call failed", exc_info=True)
        session_manager.record_event(
            "model_interpretation",
            {"purpose": "findings_summary", "fallback": True},
            source="application",
        )
        return {
            "findings": {
                "finding": "The model gateway was unavailable, so no interpreted summary could be generated.",
                "evidence_references": [
                    "selected_outlier", "applied_filters", "workspace", "registration",
                    "anomalous_wafers", "wafer_rows",
                ],
                "confidence": "low",
                "limitations": ["The findings-summary model call failed; only the raw evidence above is available."],
                "recommended_next_actions": ["Retry the investigation once the model gateway is available."],
                "alternative_explanations": [],
            }
        }


def _halted(state: InvestigationState) -> bool:
    return bool(state.get("cancelled_at"))


def build_graph():
    """Compile the investigation graph with a PostgreSQL-backed checkpointer.

    The checkpointer holds a connection pool for the process lifetime
    (auto-reconnecting, unlike a single bare connection), matching the target
    diagram's `workflow -> pg_checkpoints`.
    """
    builder = StateGraph(InvestigationState)

    builder.add_node("parse_scope", parse_scope)
    builder.add_node("confirm_absolute_threshold", confirm_absolute_threshold)
    builder.add_node("analyze_trends", analyze_trends)
    builder.add_node("confirm_investigation", confirm_investigation)
    builder.add_node("create_workspace", create_workspace)
    builder.add_node("apply_filters", apply_filters)
    builder.add_node("approve_registration", approve_registration)
    builder.add_node("register_and_wait", register_and_wait)
    builder.add_node("query_wafers", query_wafers)
    builder.add_node("summarise", summarise)

    builder.add_edge(START, "parse_scope")
    builder.add_conditional_edges(
        "parse_scope",
        lambda s: "confirm_absolute_threshold" if s.get("needs_threshold_clarification") else "analyze_trends",
        {"confirm_absolute_threshold": "confirm_absolute_threshold", "analyze_trends": "analyze_trends"},
    )
    builder.add_conditional_edges(
        "confirm_absolute_threshold",
        lambda s: END if _halted(s) else "analyze_trends",
        {END: END, "analyze_trends": "analyze_trends"},
    )
    builder.add_conditional_edges(
        "analyze_trends",
        lambda s: "confirm_investigation" if s.get("outliers") else END,
        {END: END, "confirm_investigation": "confirm_investigation"},
    )
    builder.add_conditional_edges(
        "confirm_investigation",
        lambda s: END if _halted(s) else "create_workspace",
        {END: END, "create_workspace": "create_workspace"},
    )
    builder.add_edge("create_workspace", "apply_filters")
    builder.add_edge("apply_filters", "approve_registration")
    builder.add_conditional_edges(
        "approve_registration",
        lambda s: END if _halted(s) else "register_and_wait",
        {END: END, "register_and_wait": "register_and_wait"},
    )
    builder.add_edge("register_and_wait", "query_wafers")
    builder.add_edge("query_wafers", "summarise")
    builder.add_edge("summarise", END)

    return builder.compile(checkpointer=build_checkpointer())
