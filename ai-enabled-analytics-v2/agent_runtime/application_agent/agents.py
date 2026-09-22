"""Typed PydanticAI agents: filters -> TrendFilters, intent -> DetectionScope,
evidence -> FindingsSummary.

Replaces the original demonstrator's raw
``get_llm().with_structured_output(DetectionScope).invoke(prompt)`` calls with
``pydantic_ai.Agent`` definitions (Phase 1 of PLAN.md). The model itself comes
from the foundation model gateway; only the typed output contracts and the prompt
text are application-owned and live here.

Two scope-agent variants exist, switchable per-request via ``use_tool_calling``
(threaded from the UI toggle through ``api.py``/``graph.py``):
- ``scope_agent()`` (default): the app pre-fetches empirical distribution stats
  and stuffs them into the prompt; the model never calls a tool.
- ``scope_agent_tool_calling()``: the model calls ``get_kpi_distribution_stats``
  itself, guarded by ``SCOPE_TOOL_CALLING_GUARDRAILS`` so it cannot fabricate the
  numbers a real tool call would have returned.
"""

from functools import lru_cache

from pydantic_ai import Agent

from foundation.model_gateway import get_model
from mcp_capability_adaptor import client as mcp_client

from .contracts import DetectionScope, FindingsSummary, TrendFilters

TREND_SYSTEM_PROMPT = (
    "Extract which trend-chart filters a semiconductor process engineer named in a "
    "free-text display request. Extract lookback_days from relative phrases like "
    "'last 7 days' - leave it null if the analyst instead gave an explicit date range "
    "or named no date filter at all. Extract an explicit start_date/end_date (ISO "
    "YYYY-MM-DD) only when the analyst gave an explicit date range, e.g. 'from "
    "12-02-2025 to 12-02-2026' - leave both null otherwise. Extract every lot, "
    "product, layer, or exposure equipment (machine) ID the analyst named as a list, "
    "splitting comma-separated names - leave a list empty when nothing of that kind "
    "was named. State in one short sentence which filters were applied, or that "
    "defaults were used."
)

SCOPE_SYSTEM_PROMPT = (
    "Decide how to find outliers in semiconductor wafer trends from an analyst's "
    "request, within the trend-chart filters already in effect (supplied as "
    "empirical context below - do not re-extract filters). A number with % is a "
    "percentage threshold; a unitless number is an absolute OPO KPI threshold. If "
    "they ask for outliers with no number, compare each machine against its own "
    "normal level. If the analyst did NOT name an explicit numeric threshold, also "
    "recommend an absolute OPO KPI outlier cutoff as suggested_limit_value, using "
    "only the supplied empirical context (p95, p99, mean, stdev, bell_curve_range), "
    "and explain it in suggested_limit_rationale. If the analyst DID name a number, "
    "leave suggested_limit_value and suggested_limit_rationale null."
)

# Anti-hallucination rules for the tool-calling variant: without a pre-fetched
# context in the prompt, the model has nothing to ground a suggested cutoff in
# except this tool - these rules are the only thing stopping it from guessing.
SCOPE_TOOL_CALLING_GUARDRAILS = (
    "You have a tool, get_kpi_distribution_stats, that returns REAL empirical "
    "p95/p99/mean/stdev/bell_curve_range numbers for the OPO KPI trend table. Hard rules:\n"
    "1. If you intend to fill suggested_limit_value or suggested_limit_rationale, you MUST "
    "call this tool first and use only the numbers it returns - never invent, round, or "
    "estimate a p95/p99/mean/stdev value yourself.\n"
    "2. Call it at most once, with the SAME filters already established for this "
    "investigation (given to you as context below) - never invent a different filter.\n"
    "3. If the tool returns sample_count: 0, there is no matching data: leave "
    "suggested_limit_value null and say so in suggested_limit_rationale rather than "
    "guessing a number.\n"
    "4. If the tool call fails or is unavailable, leave suggested_limit_value and "
    "suggested_limit_rationale null instead of fabricating a value.\n"
    "If the analyst does not provide a threshold:\n"
    "1. Call get_kpi_distribution_stats().\n"
    "2. Use p95 as the default recommended threshold.\n"
    "3. Use p99 only for severe anomaly detection.\n"
    "4. Set:\n"
        "suggested_limit_value\n"
        "suggested_limit_rationale\n"
    "5. Also set:\n"
        "mode='absolute'\n"
        "limit_value=<suggested_limit_value>\n"
        "direction='above'\n"
        "threshold_unit='absolute'\n"
    "6. Never leave limit_value empty.\n"
)

FINDINGS_SYSTEM_PROMPT = (
    "Summarize wafer-level investigation evidence for a semiconductor process "
    "engineer. State only what the supplied evidence supports; do not invent "
    "datasets, machines, or KPI values. Reference evidence labels exactly as given."
)


def _get_kpi_distribution_stats_tool(
    days: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
) -> dict:
    """Real p95/p99/mean/stdev/bell_curve_range stats for the OPO KPI trend table,
    filtered exactly as given. Call this before setting suggested_limit_value or
    suggested_limit_rationale - never invent those numbers. Use only the filters
    already established for this investigation, given to you as context."""
    return mcp_client.get_kpi_distribution_stats(
        days=days,
        start_date=start_date,
        end_date=end_date,
        lot_ids=lot_ids,
        product_ids=product_ids,
        layer_ids=layer_ids,
        exposure_equipment_ids=exposure_equipment_ids,
    )


@lru_cache
def trend_agent() -> Agent[None, TrendFilters]:
    """Parses an analyst's free-text display request into structured `TrendFilters`."""
    return Agent(get_model(), output_type=TrendFilters, system_prompt=TREND_SYSTEM_PROMPT)


@lru_cache
def scope_agent() -> Agent[None, DetectionScope]:
    """Parses an analyst's free-text request into a structured `DetectionScope`."""
    return Agent(get_model(), output_type=DetectionScope, system_prompt=SCOPE_SYSTEM_PROMPT)


@lru_cache
def scope_agent_tool_calling() -> Agent[None, DetectionScope]:
    """Same as `scope_agent()`, but the model calls `get_kpi_distribution_stats`
    itself instead of being pre-fed empirical context in the prompt."""
    return Agent(
        get_model(),
        output_type=DetectionScope,
        system_prompt=f"{SCOPE_SYSTEM_PROMPT}\n\n{SCOPE_TOOL_CALLING_GUARDRAILS}",
        tools=[_get_kpi_distribution_stats_tool],
    )


@lru_cache
def findings_agent() -> Agent[None, FindingsSummary]:
    """Summarizes gathered evidence into a structured `FindingsSummary`."""
    return Agent(get_model(), output_type=FindingsSummary, system_prompt=FINDINGS_SYSTEM_PROMPT)


def parse_trend_filters(question: str) -> TrendFilters:
    return trend_agent().run_sync(f"Request: {question}").output


def parse_scope(question: str, empirical_context: dict, use_tool_calling: bool = False) -> DetectionScope:
    if use_tool_calling:
        # No pre-fetched context: the model must call the tool itself to get grounded numbers.
        prompt = f"Request: {question}\n\nFilters already established for this investigation: {empirical_context}"
        result = scope_agent_tool_calling().run_sync(prompt)
        print("=== RAW RESULT ===")
        print(result)
        print("=== OUTPUT ===")
        print(result.output)
        return result.output
    prompt = f"Request: {question}\n\nEmpirical context (for the filters already established): {empirical_context}"
    return scope_agent().run_sync(prompt).output


def summarize_findings(evidence_prompt: str) -> FindingsSummary:
    return findings_agent().run_sync(evidence_prompt).output
