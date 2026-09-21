---
id: opo-investigation-agent
version: "1.0"
kind: agent
defaults:
  limit_value: 3.0
  baseline_deviation_pct: 3.0
models:
  TrendFilters:
    fields:
      lookback_days: {type: optional_int, default: null, description: "Relative lookback in days."}
      start_date: {type: optional_string, default: null, description: "Inclusive ISO start date."}
      end_date: {type: optional_string, default: null, description: "Inclusive ISO end date."}
      lot_ids: {type: string_list, default: [], description: "Lot identifiers."}
      product_ids: {type: string_list, default: [], description: "Product identifiers."}
      layer_ids: {type: string_list, default: [], description: "Layer identifiers."}
      exposure_equipment_ids: {type: string_list, default: [], description: "Exposure equipment identifiers."}
      interpretation: {type: string, default: "", description: "Short filter interpretation."}
  DetectionScope:
    fields:
      mode: {type: literal, values: [absolute, baseline], default: baseline, description: "Outlier detection mode."}
      limit_value: {type: float, default: 3.0, description: "KPI threshold."}
      direction: {type: literal, values: [below, above], default: below, description: "Comparison direction."}
      threshold_unit: {type: literal, values: [percent, absolute], default: percent, description: "Threshold unit."}
      baseline_deviation_pct: {type: optional_float, default: null, description: "Baseline deviation percentage."}
      interpretation: {type: string, default: "", description: "Short interpretation."}
      suggested_limit_value: {type: optional_float, default: null, description: "Recommended absolute cutoff."}
      suggested_limit_rationale: {type: optional_string, default: null, description: "Recommendation rationale."}
  FindingsSummary:
    fields:
      finding: {type: string, default: "", description: "Evidence-based finding."}
      evidence_references: {type: string_list, default: [], description: "Evidence labels."}
      confidence: {type: literal, values: [low, medium, high], default: low, description: "Finding confidence."}
      limitations: {type: string_list, default: [], description: "Important limitations."}
      recommended_next_actions: {type: string_list, default: [], description: "Evidence-grounded next actions."}
      alternative_explanations: {type: string_list, default: [], description: "Explanations not ruled out."}
prompts:
  trend_filters: |
    Extract trend filters from the analyst request. Do not invent identifiers.
  detection_scope: |
    Interpret the outlier request using the supplied KPI distribution context. Explicit numeric thresholds take precedence.
  findings_summary: |
    Summarize only the supplied investigation evidence. Do not invent identifiers, causes, measurements, or time ranges.
evidence_labels:
  - selected_outlier
  - applied_filters
  - workspace
  - registration
  - anomalous_wafers
  - wafer_rows
---

# OPO Investigation Agent Definition

The OPO Investigation Agent interprets trend filters and outlier intent, then produces evidence-bounded findings. Model calls interpret or summarize only; deterministic application code owns data access, trend analysis, and side effects.

## Guardrails

- Do not invent KPI definitions, datasets, identifiers, causes, or measurements.
- Do not access platform data stores directly.
- Use only governed capabilities for side effects.
- Restrict findings evidence references to the labels declared above.
