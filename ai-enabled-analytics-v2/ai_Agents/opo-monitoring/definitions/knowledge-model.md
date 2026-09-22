---
id: opo-investigation-knowledge
version: "1.0"
kind: knowledge-model
---

# OPO Investigation Knowledge Model

Application-owned knowledge includes KPI definitions, trend semantics, outlier meaning, filters, and evidence interpretation. Foundation-owned knowledge includes dataset identity, workspace state, registration state, governed service APIs, checkpoint state, and audit events.

## Evidence Labels

- `selected_outlier`: analyst-approved candidate.
- `applied_filters`: filters sent to the workspace.
- `workspace`: created workspace identifier.
- `registration`: dataset readiness and table.
- `anomalous_wafers`: flagged wafer records.
- `wafer_rows`: summarized and sampled wafer data.

A plausible explanation is not a confirmed cause. Findings must be grounded in returned evidence.
