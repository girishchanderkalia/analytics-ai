---
id: opo-investigation-workflow
version: "1.0"
kind: workflow
max_registration_polls: 10
entry_node: parse_trend_request
nodes:
  - id: parse_trend_request
    type: model
    prompt: trend_filters
    output: TrendFilters
  - id: analyze_trends
    type: capability
    capability: data_query.read_trends
  - id: investigate_outlier
    type: approval
    approval: investigate_outlier
  - id: summarize_findings
    type: model
    prompt: findings_summary
    output: FindingsSummary
edges:
  - from: parse_trend_request
    to: analyze_trends
  - from: analyze_trends
    to: investigate_outlier
  - from: investigate_outlier
    to: summarize_findings
routing:
  defaults:
    analyze_trends: investigate_outlier
    investigate_outlier: summarize_findings
  conditions:
    - from: analyze_trends
      when: "outliers == []"
      to: summarize_findings
    - from: investigate_outlier
      when: "cancelled_at != null"
      to: END
approvals:
  - id: investigate_outlier
    required: true
    decision_field: investigation_approved
---

# OPO Investigation Workflow Definition

The workflow is a resumable four-step conversation:

1. Parse trend filters and fetch the trend series.
2. Wait for an outlier command; clarify a recommended threshold when no explicit number was supplied.
3. Analyze trends deterministically, obtain analyst approval, create a workspace, apply filters, register `overlay_wafer_points`, and query wafers.
4. Summarize supplied evidence and offer supported next actions.

Human gates are the command wait, threshold clarification, outlier investigation approval, and next-action selection. Registration is internal plumbing and runs automatically after investigation approval. Registration timeout occurs after `max_registration_polls` polls.
