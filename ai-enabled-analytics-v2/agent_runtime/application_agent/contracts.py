"""Typed contracts between the workflow and the application agent layer.

Ported unchanged (field-for-field) from the original demonstrator's
``ApplicationUI/analytics_agents/opo_monitoring_service/application_workflow.py``
so behavior is equivalent; only the module location and the fact that they now
back ``pydantic_ai.Agent`` output types (instead of
``AzureChatOpenAI.with_structured_output``) has changed.
"""

from typing import Literal

from pydantic import BaseModel, Field

DEFAULT_LIMIT_VALUE = 3.0
DEFAULT_BASELINE_DEVIATION_PCT = 3.0


class DetectionScope(BaseModel):
    """How the analyst asked for outliers to be identified."""

    mode: Literal["absolute", "baseline"] = Field(
        description=(
            "Use 'absolute' when the analyst names a KPI threshold, e.g. 'outliers "
            "below 3.0' or 'anything above 3.2'. Use 'baseline' when they ask for "
            "outliers without naming a number, meaning each machine should be compared "
            "against its own normal level."
        )
    )
    limit_value: float = Field(
        description=(
            "The KPI threshold named by the analyst, used only when mode is "
            f"'absolute'. If no number was named, use {DEFAULT_LIMIT_VALUE}."
        )
    )
    direction: Literal["below", "above"] = Field(
        description=(
            "Which side of the limit to mark, used only when mode is 'absolute'. "
            "'below' for under/below/less than/worse than, 'above' for over/above/"
            "more than/better than. Default 'below'."
        )
    )
    threshold_unit: Literal["percent", "absolute"] = Field(
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
    lookback_days: int = Field(default=14, description="Number of most recent days to include, default 14.")
    machine_id: str | None = Field(default=None, description="Machine or exposure equipment ID filter, if named.")
    lot_id: str | None = Field(default=None, description="Lot ID filter, if named.")
    product_id: str | None = Field(default=None, description="Product ID filter, if named.")
    layer_id: str | None = Field(default=None, description="Layer ID filter, if named.")
    exposure_equipment_id: str | None = Field(default=None, description="Exposure equipment ID filter, if named.")
    suggested_limit_value: float | None = Field(
        default=None,
        description=(
            "Only when the analyst did not name an explicit numeric threshold: an absolute "
            "OPO KPI outlier cutoff recommended from the supplied empirical P95/P99 context. "
            "Prefer P95 for a broader screening threshold or P99 for severe anomalies. Null "
            "when the analyst already named a number."
        ),
    )
    suggested_limit_rationale: str | None = Field(
        default=None,
        description=(
            "One short explanation for suggested_limit_value, grounded only in the supplied "
            "P95/P99 values. Null when suggested_limit_value is null."
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
