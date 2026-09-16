"""Typed PydanticAI agents: intent -> DetectionScope, evidence -> FindingsSummary.

Replaces the original demonstrator's raw
``get_llm().with_structured_output(DetectionScope).invoke(prompt)`` calls with
``pydantic_ai.Agent`` definitions (Phase 1 of PLAN.md). The model itself comes
from the foundation model gateway; only the typed output contract and the prompt
text are application-owned and live here.
"""

from functools import lru_cache

from pydantic_ai import Agent

from foundation.model_gateway import get_model

from .contracts import DetectionScope, FindingsSummary

SCOPE_SYSTEM_PROMPT = (
    "Decide how to find outliers in semiconductor wafer trends from an analyst's "
    "request. A number with % is a percentage threshold; a unitless number is an "
    "absolute OPO KPI threshold. If they ask for outliers with no number, compare "
    "each machine against its own normal level. Extract lookback_days from phrases "
    "like 'last 7 days' and extract any named machine, lot, product, layer, or "
    "exposure equipment filters. If the analyst did NOT name an explicit numeric "
    "threshold, also recommend an absolute OPO KPI outlier cutoff as "
    "suggested_limit_value, using only the supplied empirical context, and explain "
    "it in suggested_limit_rationale. If the analyst DID name a number, leave "
    "suggested_limit_value and suggested_limit_rationale null."
)

FINDINGS_SYSTEM_PROMPT = (
    "Summarize wafer-level investigation evidence for a semiconductor process "
    "engineer. State only what the supplied evidence supports; do not invent "
    "datasets, machines, or KPI values. Reference evidence labels exactly as given."
)


@lru_cache
def scope_agent() -> Agent[None, DetectionScope]:
    """Parses an analyst's free-text request into a structured `DetectionScope`."""
    return Agent(get_model(), output_type=DetectionScope, system_prompt=SCOPE_SYSTEM_PROMPT)


@lru_cache
def findings_agent() -> Agent[None, FindingsSummary]:
    """Summarizes gathered evidence into a structured `FindingsSummary`."""
    return Agent(get_model(), output_type=FindingsSummary, system_prompt=FINDINGS_SYSTEM_PROMPT)


def parse_scope(question: str, empirical_context: dict) -> DetectionScope:
    prompt = f"Request: {question}\n\nEmpirical context (last 14 days, all machines): {empirical_context}"
    return scope_agent().run_sync(prompt).output


def summarize_findings(evidence_prompt: str) -> FindingsSummary:
    return findings_agent().run_sync(evidence_prompt).output
