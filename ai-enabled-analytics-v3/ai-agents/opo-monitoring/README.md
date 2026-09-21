# OPO Monitoring Agent

The OPO Monitoring Agent supports conversational investigation of OPO KPI
trends, candidate outliers, and wafer-level evidence.

The agent is owned by the OPO Monitoring application and is described using
declarative Markdown definitions. The shared Application Agent Runtime loads,
validates, and executes these definitions.

## Application ownership

The OPO Monitoring application owns:

- OPO terminology and domain knowledge
- KPI meaning
- trend semantics
- outlier interpretation
- relevant business filters
- relevant analytical data
- investigation workflow intent
- application-specific state
- prompts
- structured model contracts
- evidence interpretation
- required Analytics Foundation capabilities

## Shared runtime ownership

The Application Agent Runtime owns:

- agent discovery
- definition loading
- definition validation
- contract generation
- workflow construction
- LangGraph integration
- model invocation
- deterministic operation invocation
- capability dispatch
- capability request mapping
- capability result mapping
- approval interrupts
- conversation persistence
- workflow checkpoints
- workflow resume
- runtime telemetry

## Analytics Foundation ownership

Analytics Foundation owns:

- Workspace API
- Data Query API
- Query Engine API
- Asset API
- Processing API
- governed data access
- governed platform operations

Analytics Foundation does not own:

- agent definitions
- LangGraph workflows
- conversation state
- workflow checkpoints
- agent approvals
- capability mapping
- Copilot interaction logic

## Definition files

```text
definitions/
├── agent-definition.md
├── workflow-definition.md
├── state-model.md
├── tools-and-capabilities.md
├── knowledge-model.md
└── sequence-diagrams.md
```

## Existing application interaction

The existing application interaction remains independent of the agent runtime:

```text
OPO Monitoring FE
    -> OPO Monitoring Service
        -> Analytics Foundation APIs
```

The OPO Monitoring Service calls Analytics Foundation APIs directly for
existing deterministic application functions.

## Copilot interaction

The conversational interaction uses the shared platform path:

```text
Analytics Copilot FE
    -> Analytics Copilot Service
        -> Application Agent Runtime