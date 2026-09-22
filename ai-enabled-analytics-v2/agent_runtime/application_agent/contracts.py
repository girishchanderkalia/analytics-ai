"""Typed contracts between the workflow and the application agent layer.

``DetectionScope`` and ``FindingsSummary`` were ported unchanged (field-for-field)
from the original demonstrator's
``ApplicationUI/analytics_agents/opo_monitoring_service/application_workflow.py``.
``TrendFilters`` is new: the 4-step conversational workflow (trend display -> outlier
detection -> outlier selection -> deep-dive) parses trend-chart filters once, up
front, separately from outlier intent - so ``DetectionScope`` no longer carries
filter fields; it only carries how to detect outliers within whatever filters
``TrendFilters`` already established.
"""

from typing import Literal

from pydantic import BaseModel, Field

DEFAULT_LIMIT_VALUE = 3.0
DEFAULT_BASELINE_DEVIATION_PCT = 3.0


class TrendFilters(BaseModel):
    """Which trend-chart filters the analyst named, from a free-text display request."""

    lookback_days: int | None = Field(
        default=None,
        description=(
            "Relative lookback in days, e.g. 7 for 'last 7 days'. Null when the analyst "
            "gave an explicit date range instead, or named no date filter at all (then "
            "the default of 14 days is used)."
        ),
    )
    start_date: str | None = Field(
        default=None,
        description=(
            "Explicit ISO date (YYYY-MM-DD) range start, only when the analyst named an "
            "explicit date range (e.g. 'from 12-02-2025 to 12-02-2026') instead of a "
            "relative lookback. Null otherwise."
        ),
    )
    end_date: str | None = Field(
        default=None,
        description="Explicit ISO date (YYYY-MM-DD) range end, paired with start_date. Null otherwise.",
    )
    lot_ids: list[str] = Field(
        default_factory=list,
        description="Lot IDs named by the analyst (e.g. 'lot1, lot2, lot3'). Empty list means all lots.",
    )
    product_ids: list[str] = Field(
        default_factory=list, description="Product IDs named by the analyst. Empty list means all products."
    )
    layer_ids: list[str] = Field(
        default_factory=list, description="Layer IDs named by the analyst. Empty list means all layers."
    )
    exposure_equipment_ids: list[str] = Field(
        default_factory=list,
        description="Exposure equipment (machine) IDs named by the analyst. Empty list means all machines.",
    )
    interpretation: str = Field(
        description="One short sentence stating which filters were applied, or that defaults were used."
    )


class DetectionScope(BaseModel):
    """How the analyst asked for outliers to be identified, within the trend filters
    already established by ``TrendFilters``."""

    mode: Literal["absolute", "baseline"] = Field(
        description=(
            "Use 'absolute' when the analyst names a KPI threshold, e.g. 'outliers "
            "below 3.0' or 'anything above 3.2'. Use 'baseline' when they ask for "
            "outliers without naming a number, meaning each machine should be compared "
            "against its own normal level."
        )
    )
    limit_value: float | None = Field(
        description=(
            "The KPI threshold named by the analyst, used only when mode is "
            f"'absolute'. If no number was named, use {DEFAULT_LIMIT_VALUE}."
        )
    )
    direction: Literal["below", "above"] | None = Field(
        description=(
            "Which side of the limit to mark, used only when mode is 'absolute'. "
            "'below' for under/below/less than/worse than, 'above' for over/above/"
            "more than/better than. Default 'below'."
        )
    )
    threshold_unit: Literal["percent", "absolute"] | None = Field(
        description=(
            "Unit for a numeric threshold: use 'percent' for a relative deviation, "
            "otherwise use 'absolute' for the OPO KPI value."
        )
    )
    baseline_deviation_pct: float | None = Field(
        description=(
            "Percentage deviation above a machine's own median that counts as abnormal, "
            "used only when mode is 'baseline'. Return null when the analyst did not specify it."
        )
    )
    interpretation: str = Field(
        description=(
            "One short sentence stating how the request was read, including which "
            "rule was applied, so the analyst can check it."
        )
    )
    suggested_limit_value: float | None = Field(
        default=None,
        description=(
            "Only when the analyst did not name an explicit numeric threshold: an absolute "
            "OPO KPI outlier cutoff recommended from the supplied empirical context (p95, "
            "p99, mean, stdev, bell_curve_range). Prefer p95 for a broader screening "
            "threshold, p99 for severe anomalies, or the bell_curve_range upper bound when "
            "the distribution's spread is wide. Null when the analyst already named a number."
        ),
    )
    suggested_limit_rationale: str | None = Field(
        default=None,
        description=(
            "One short explanation for suggested_limit_value, grounded only in the supplied "
            "p95/p99/mean/stdev/bell_curve_range values. Null when suggested_limit_value is "
            "null."
        ),
    )


class FindingsSummary(BaseModel):
    finding: str = Field(description="One concise finding, stated only from the supplied evidence.")
    evidence_references: list[str] = Field(
        description="Evidence labels supporting the finding, chosen from the labels supplied in the prompt."
    )
    confidence: Literal["low", "medium", "high"]
    limitations: list[str] = Field(description="Important limitations or missing data that affect interpretation.")
    recommended_next_actions: list[str] = Field(description="Concrete next actions grounded in the evidence.")
    alternative_explanations: list[str] = Field(description="Plausible alternatives that are not ruled out by the evidence.")
