---
id: opo-investigation-state
version: "1.0"
kind: state-model
fields:
    question: {type: string, default: ""}
    trend_filters: {type: object, default: {}}
    trend_series: {type: object_list, default: []}
    analysis: {type: object_list, default: []}
    outliers: {type: object_list, default: []}
    selected_outlier: {type: object, default: null}
    investigation_approved: {type: boolean, default: false}
    findings: {type: object, default: null}
    cancelled_at: {type: optional_string, default: null}
---

# OPO Investigation State Model

State contains the analyst request, parsed filters, detection rule, threshold context, trend series, deterministic analysis, outliers, selected candidate, workspace and filter evidence, registration history, wafer data, findings, selected action, spatial pattern, and cancellation reason.

## Lifecycle

```mermaid
stateDiagram-v2
    [*] --> TrendParsed
    TrendParsed --> AwaitCommand
    AwaitCommand --> OutlierParsed
    OutlierParsed --> ThresholdClarification
    ThresholdClarification --> TrendsAnalyzed
    OutlierParsed --> TrendsAnalyzed
    TrendsAnalyzed --> InvestigationApproval
    TrendsAnalyzed --> [*]: no outliers
    InvestigationApproval --> Workspace
    Workspace --> Registration
    Registration --> WaferEvidence
    WaferEvidence --> Findings
    Findings --> FollowUp
    FollowUp --> [*]
```

Checkpoints make interrupts resumable. Secrets do not belong in workflow state.
