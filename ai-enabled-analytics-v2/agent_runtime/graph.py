"""Investigation workflow orchestration (Phase 1 + 3 of PLAN.md).

Ported from the original demonstrator's ``application_workflow.py``. The pipeline
is deterministic, so each mechanical step is a code node rather than a tool call
the model could skip or fabricate. Application agents (typed PydanticAI agents)
are used only to interpret intent and summarize findings. Human gates are
``interrupt()`` points, resumable via the PostgreSQL-backed checkpointer.

4-step conversational flow (one open thread spans all steps, via repeated
``/resume`` calls carrying the analyst's next free-text message):
  1. ``parse_trend_request`` parses display filters and shows the trend chart -
     no approval needed, since displaying data draws no conclusion.
  2. ``await_next_command`` pauses for the analyst's next message. If it names
     an explicit numeric threshold, ``parse_outlier_command`` applies it directly;
     otherwise ``confirm_absolute_threshold`` asks the analyst to approve a
     model-suggested cutoff first.
  3. ``confirm_investigation`` asks the analyst to approve/pick one of the
     flagged outliers, then the deep-dive (workspace/registration/wafer query)
     runs automatically - no approval for workspace creation or dataset
     registration, since that is internal plumbing, not an analyst decision.
  4. ``summarise`` produces the findings, then ``offer_next_actions`` asks the
     analyst which of the model's own recommended next actions to take.

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
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from agent_runtime.application_agent.agents import parse_scope as agent_parse_scope
from agent_runtime.application_agent.agents import parse_trend_filters, summarize_findings
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
    next_command: str | None
    use_tool_calling: bool
    lookback_days: int | None
    start_date: str | None
    end_date: str | None
    lot_ids: list[str]
    product_ids: list[str]
    layer_ids: list[str]
    exposure_equipment_ids: list[str]
    mode: str
    limit_value: float
    requested_limit_value: float
    direction: str
    threshold_unit: str
    baseline_deviation_pct: float
    interpretation: str
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
    selected_action: str | None
    spatial_pattern: dict
    cancelled_at: str


def _is_approved(decision: Any) -> bool:
    if isinstance(decision, dict):
        return bool(decision.get("approved", True))
    if isinstance(decision, str):
        return decision.strip().lower() in {"y", "yes", "approve", "approved", "true"}
    return bool(decision)


def _filter_kwargs(state: InvestigationState) -> dict[str, Any]:
    """The trend-chart filters established in step 1, reused by every later step."""
    return {
        "days": state.get("lookback_days"),
        "start_date": state.get("start_date"),
        "end_date": state.get("end_date"),
        "lot_ids": state.get("lot_ids"),
        "product_ids": state.get("product_ids"),
        "layer_ids": state.get("layer_ids"),
        "exposure_equipment_ids": state.get("exposure_equipment_ids"),
    }


def parse_trend_request(state: InvestigationState) -> InvestigationState:
    """Step 1: parse trend-chart filters from free text and display the chart.

    No ``interrupt()`` here - displaying data draws no conclusion, so it needs no
    approval. The analyst's next message is collected separately by
    ``await_next_command`` below.
    """
    question = state.get("next_command") or state.get("question", "")

    lookback_days: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    lot_ids: list[str] = []
    product_ids: list[str] = []
    layer_ids: list[str] = []
    exposure_equipment_ids: list[str] = []
    interpretation = "No filters named, so the default last 14 days across all lots/products/layers/machines is shown."

    try:
        with session_manager.timed_event("model_call", {"purpose": "trend_filter_interpretation"}):
            filters = parse_trend_filters(question)
        lookback_days = filters.lookback_days
        start_date = filters.start_date
        end_date = filters.end_date
        lot_ids = filters.lot_ids
        product_ids = filters.product_ids
        layer_ids = filters.layer_ids
        exposure_equipment_ids = filters.exposure_equipment_ids
        interpretation = filters.interpretation
        session_manager.record_event(
            "model_interpretation",
            {"request": question, "interpretation": filters.model_dump()},
            source="application",
        )
    except Exception:
        log.warning("Could not parse trend filters from %r; using defaults", question, exc_info=True)
        session_manager.record_event(
            "model_interpretation",
            {"request": question, "interpretation": "fallback_defaults", "fallback": True},
            source="application",
        )

    if lookback_days is not None:
        lookback_days = min(max(int(lookback_days), 1), 90)

    trend_series = services.get_trend_series(
        days=lookback_days,
        start_date=start_date,
        end_date=end_date,
        lot_ids=lot_ids,
        product_ids=product_ids,
        layer_ids=layer_ids,
        exposure_equipment_ids=exposure_equipment_ids,
    )

    return {
        "question": question,
        "lookback_days": lookback_days,
        "start_date": start_date,
        "end_date": end_date,
        "lot_ids": lot_ids,
        "product_ids": product_ids,
        "layer_ids": layer_ids,
        "exposure_equipment_ids": exposure_equipment_ids,
        "interpretation": interpretation,
        "trend_series": trend_series,
    }


def await_next_command(state: InvestigationState) -> InvestigationState:
    """Pause and wait for the analyst's next free-text message.

    Kept minimal - the interrupt is the first statement - so resuming does not
    re-run any model call. The resumed value can be a plain string or
    ``{"message": "..."}``; either way it becomes ``next_command``.
    """
    trend_series = state.get("trend_series") or []
    decision = interrupt(
        {
            "type": "await_next_command",
            "question": (
                "Trend chart ready. What would you like to do next? "
                "(e.g. 'show outliers', 'show outliers above 3', or refine the filters)"
            ),
            "series_count": len(trend_series),
            "point_count": sum(len(s.get("points", [])) for s in trend_series),
        }
    )
    text = decision.get("message") if isinstance(decision, dict) else str(decision or "")
    return {"next_command": text}


_OUTLIER_KEYWORDS = ("outlier", "anomal", "extreme")


def _mentions_outliers(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _OUTLIER_KEYWORDS)


def parse_outlier_command(state: InvestigationState) -> InvestigationState:
    """Step 2: interpret an outlier-detection request, within the filters step 1
    already established.

    Does not itself call ``interrupt()``: LangGraph re-executes a node's entire
    function body (including any LLM calls) from the top every time that node
    resumes from an interrupt, so the interrupt for an absolute-threshold
    clarification lives in the separate, minimal ``confirm_absolute_threshold``
    node below instead.
    """
    question = state.get("next_command") or state.get("question", "")
    use_tool_calling = bool(state.get("use_tool_calling", False))
    filter_kwargs = _filter_kwargs(state)

    mode = "baseline"
    limit = DEFAULT_LIMIT_VALUE
    direction = "below"
    threshold_unit = "percent"
    deviation = DEFAULT_BASELINE_DEVIATION_PCT
    interpretation = (
        f"No limit named, so each machine is compared against its own median "
        f"({DEFAULT_BASELINE_DEVIATION_PCT}% increase counts as abnormal)."
    )

    threshold_context: dict[str, Any] = {}
    threshold_recommendation: dict[str, Any] = {}
    suggested_limit_value: float | None = None
    suggested_limit_rationale: str | None = None
    # Computed up front, from the filters already established in step 1, with no LLM
    # call, so the single model call below can recommend a cutoff in the same response.
    threshold_context = services.get_kpi_threshold_context(**filter_kwargs)
    try:
        with session_manager.timed_event("model_call", {"purpose": "outlier_interpretation"}):
            scope = agent_parse_scope(question, threshold_context, use_tool_calling=use_tool_calling)
        mode = scope.mode
        limit = float(scope.limit_value)
        direction = scope.direction
        threshold_unit = scope.threshold_unit
        deviation = float(scope.baseline_deviation_pct or DEFAULT_BASELINE_DEVIATION_PCT)
        interpretation = scope.interpretation
        suggested_limit_value = scope.suggested_limit_value
        suggested_limit_rationale = scope.suggested_limit_rationale
        session_manager.record_event(
            "model_interpretation",
            {"request": question, "interpretation": scope.model_dump(), "use_tool_calling": use_tool_calling},
            source="application",
        )
    except Exception:
        log.warning("Could not parse outlier command from %r; using default", question, exc_info=True)
        session_manager.record_event(
            "model_interpretation",
            {"request": question, "interpretation": "fallback_defaults", "fallback": True, "use_tool_calling": use_tool_calling},
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

    if not threshold_match:
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
        "threshold_context": threshold_context,
        "threshold_recommendation": threshold_recommendation,
        "needs_threshold_clarification": False,
    }


def confirm_absolute_threshold(state: InvestigationState) -> InvestigationState:
    """Ask the analyst to accept or edit the recommended absolute KPI cutoff.

    Kept minimal - the interrupt is the first real statement - because LangGraph
    re-executes a node's whole function body from the top on every resume from an
    interrupt; if the LLM call from ``parse_outlier_command`` lived here too,
    accepting the threshold would re-run that model call (and its latency) again.
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
    filter_kwargs = _filter_kwargs(state)
    analysis = services.analyse_series(
        mode=state.get("mode", "baseline"),
        limit_value=state.get("limit_value", DEFAULT_LIMIT_VALUE),
        direction=state.get("direction", "below"),
        limit_unit=state.get("threshold_unit", "percent"),
        baseline_deviation_pct=state.get("baseline_deviation_pct", DEFAULT_BASELINE_DEVIATION_PCT),
        **filter_kwargs,
    )
    # Already fetched once in step 1 (parse_trend_request); reuse it instead of a
    # second identical MCP round trip.
    trend_series = state.get("trend_series") or services.get_trend_series(**filter_kwargs)
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
    exposure_equipment_ids = state.get("exposure_equipment_ids") or []
    wafer_filters = {
        "machine": exposure_equipment_ids[0] if exposure_equipment_ids else outliers[0]["machine"],
        "layer_id": (state.get("layer_ids") or [None])[0],
    }
    lot_ids = state.get("lot_ids") or []
    if lot_ids:
        wafer_filters["lot_ids"] = lot_ids
    elif outliers[0].get("outlier_lot_ids"):
        wafer_filters["lot_ids"] = outliers[0]["outlier_lot_ids"]
    wafer_data = services.query_wafer_data("TREND_PREVIEW", wafer_table, wafer_filters)
    return {"analysis": analysis, "outliers": outliers, "trend_series": trend_series, "wafer_data": wafer_data}


def confirm_investigation(state: InvestigationState) -> InvestigationState:
    """Step 3: ask the analyst to approve/pick one of the flagged outliers."""
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


def register_and_wait(state: InvestigationState) -> InvestigationState:
    """Workspace creation and dataset registration run automatically - this is
    internal system plumbing, not an analyst decision, so there is no approval gate
    here. A registration failure/timeout still surfaces as a real error."""
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


_SPATIAL_ACTION_KEYWORDS = ("spatial", "overlay map", "overlay vector", "edge", "x/y", "radial")


def _is_spatial_action(action: str) -> bool:
    lowered = action.lower()
    return any(keyword in lowered for keyword in _SPATIAL_ACTION_KEYWORDS)


def offer_next_actions(state: InvestigationState) -> InvestigationState:
    """Step 4: let the analyst pick one of the model's own recommended next actions.

    Only ``analyze_wafer_spatial_pattern`` below is actually automated today; picking
    any other action just ends the investigation with that choice on record - it does
    not fabricate a capability that does not exist.
    """
    actions = list((state.get("findings") or {}).get("recommended_next_actions") or [])
    options = actions + ["End investigation"]
    decision = interrupt(
        {
            "type": "select_next_action",
            "question": "Which follow-up action would you like to take?",
            "options": options,
        }
    )
    selected = decision.get("action") if isinstance(decision, dict) else decision
    if not selected or selected not in actions:
        return {"selected_action": None}
    return {"selected_action": selected}


def analyze_wafer_spatial_pattern(state: InvestigationState) -> InvestigationState:
    """Deterministic edge-vs-center classification of the anomalous wafers already
    fetched - no new model call, since this is a real coordinate computation."""
    wafer_data = state.get("wafer_data") or {}
    pattern = services.classify_wafer_spatial_pattern(
        wafer_data.get("rows", []), wafer_data.get("anomalous_wafers", [])
    )
    session_manager.record_event("spatial_pattern_analysis", pattern, source="application")
    return {"spatial_pattern": pattern}


def build_graph():
    """Compile the investigation graph with a PostgreSQL-backed checkpointer.

    The checkpointer holds a connection pool for the process lifetime
    (auto-reconnecting, unlike a single bare connection), matching the target
    diagram's `workflow -> pg_checkpoints`.
    """
    builder = StateGraph(InvestigationState)

    builder.add_node("parse_trend_request", parse_trend_request)
    builder.add_node("await_next_command", await_next_command)
    builder.add_node("parse_outlier_command", parse_outlier_command)
    builder.add_node("confirm_absolute_threshold", confirm_absolute_threshold)
    builder.add_node("analyze_trends", analyze_trends)
    builder.add_node("confirm_investigation", confirm_investigation)
    builder.add_node("create_workspace", create_workspace)
    builder.add_node("apply_filters", apply_filters)
    builder.add_node("register_and_wait", register_and_wait)
    builder.add_node("query_wafers", query_wafers)
    builder.add_node("summarise", summarise)
    builder.add_node("offer_next_actions", offer_next_actions)
    builder.add_node("analyze_wafer_spatial_pattern", analyze_wafer_spatial_pattern)

    builder.add_edge(START, "parse_trend_request")
    builder.add_conditional_edges(
        "parse_trend_request",
        # If the very same message already asked about outliers, skip waiting for a
        # separate follow-up message - handles both the 2-message and 1-message flows.
        lambda s: "parse_outlier_command" if _mentions_outliers(s.get("question", "")) else "await_next_command",
        {"parse_outlier_command": "parse_outlier_command", "await_next_command": "await_next_command"},
    )
    builder.add_conditional_edges(
        "await_next_command",
        lambda s: "parse_outlier_command" if _mentions_outliers(s.get("next_command") or "") else "parse_trend_request",
        {"parse_outlier_command": "parse_outlier_command", "parse_trend_request": "parse_trend_request"},
    )
    builder.add_conditional_edges(
        "parse_outlier_command",
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
    builder.add_edge("apply_filters", "register_and_wait")
    builder.add_edge("register_and_wait", "query_wafers")
    builder.add_edge("query_wafers", "summarise")
    builder.add_edge("summarise", "offer_next_actions")
    builder.add_conditional_edges(
        "offer_next_actions",
        lambda s: "analyze_wafer_spatial_pattern" if s.get("selected_action") and _is_spatial_action(s["selected_action"]) else END,
        {END: END, "analyze_wafer_spatial_pattern": "analyze_wafer_spatial_pattern"},
    )
    builder.add_edge("analyze_wafer_spatial_pattern", END)

    return builder.compile(checkpointer=build_checkpointer())

