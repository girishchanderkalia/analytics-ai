# OSS-Aligned Target Architecture: Migration Plan

## Objective

Align the current demonstrator with the target architecture in `agentWorkflows/mcp-oss-target-architecture.puml` while preserving the application-owned semantics and the current user workflow. The migration keeps the OPO investigation flow intact, but changes the runtime boundaries so that:

- application semantics remain in the OPO application layer;
- LangGraph stays the orchestration engine;
- MCP tools become the governed entry point to Analytics Foundation services;
- PostgreSQL is the single runtime state store for checkpoints and session/audit/memory data.

## Architectural guardrails

The target architecture makes two ownership boundaries explicit:

1. Application-owned
   - KPI definitions and dashboard semantics
   - trend and outlier interpretation
   - investigation workflow and human review decisions
   - dataset filters and evidence meaning
   - OPO domain logic in `ApplicationUI/analytics_agents/opo_monitoring_service/services.py`

2. Foundation-owned
   - model connectivity and credential handling
   - runtime orchestration and checkpointing
   - capability/tool governance
   - workspace, query, processing, and asset API integration
   - session, audit, and memory persistence

This is consistent with the repo guidance in `.github/copilot-instructions.md`: the application owns business semantics, while Analytics Foundation owns deterministic runtime capabilities.

## Target state

```text
Application UI / BFF
  -> LangGraph workflow
      -> PydanticAI application agents
      -> MCP capability adaptor
          -> Analytics Foundation APIs / StarRocks / workload services
      -> PostgreSQL runtime state
          -> LangGraph checkpoints
          -> sessions / audit / memory / workspace registrations
```

## Migration principles

- Do not move OPO business semantics into `AnalyticsFoundation/`.
- Keep `services.py` responsible for pure domain computation, not API access.
- Move side-effecting data access behind MCP tool calls.
- Keep the current BFF and UI behavior stable while the agent path becomes more platform-aligned.
- Treat PostgreSQL as the single source of truth for runtime state and evidence storage.

## Migration phases and scope

### Phase 1: Normalize the application agent layer

Goal: make the application agent structure match the target architecture without changing business behavior.

Changes:
- Move the model-facing logic into an `application_agent/` package under `ApplicationUI/analytics_agents/opo_monitoring_service/`.
- Replace raw structured-output LLM calls with `pydantic_ai.Agent` definitions.
- Keep `application_workflow.py` as the orchestration wrapper only.
- Keep `DetectionScope` and `FindingsSummary` as the contract between the workflow and the agent layer.

Deliverables:
- `ApplicationUI/analytics_agents/opo_monitoring_service/application_agent/agents.py`
- typed agent usage in the graph
- model gateway abstraction returning a PydanticAI model

Exit criteria:
- workflow behavior is unchanged from the current investigation flow;
- the model contract is typed and validated;
- no OPO-specific logic lives in the foundation runtime.

### Phase 2: Move runtime state to PostgreSQL

Goal: replace the current split SQLite usage with the PostgreSQL-backed runtime described by the target architecture.

Changes:
- Replace `SqliteSaver` with `langgraph.checkpoint.postgres.PostgresSaver`.
- Move `session_memory.py` event storage into PostgreSQL.
- Add durable tables for:
  - `sessions`
  - `agent_session_events`
  - `workspace_registrations`
  - `memory`
- Keep LangGraph checkpoint tables and session/audit tables as separate concerns, not a merged single database object.

Deliverables:
- PostgreSQL schema and initialization scripts
- migration path from local SQLite state to Postgres
- configuration updates in `run.sh` / environment setup

Exit criteria:
- graph resumes continue to work across restarts;
- evidence events survive process restarts;
- the application has one runtime-state store instead of project-local SQLite files.

### Phase 3: Introduce the MCP capability layer

Goal: shift workflow-side API access behind MCP tools and remove custom-tool invocation logic from the orchestration path.

Changes:
- Add thin MCP server boundaries for:
  - StarRocks MCP
  - Analytics API MCP
  - Kafka MCP stub
  - Hive MCP stub
- Keep the existing `AnalyticsFoundation` client modules as the implementation behind the MCP adapters.
- Route workflow tool calls through MCP, not directly through `capability_registry.invoke(...)`.
- Retain `interrupt()` as the human approval gate before high-risk tool actions.

Target mapping:
- `workspace_client.py` -> Analytics API MCP
- `query_engine_client.py` -> Analytics API MCP
- `processing_client.py` -> Analytics API MCP
- `lanadb_query.py` / `datawarehouse.py` -> StarRocks MCP
- future Kafka/Hive integrations -> stub MCP boundaries only

Deliverables:
- MCP server scaffolding and tool definitions
- workflow node updates to call MCP-backed operations
- separation of fetch operations from pure domain computation in `services.py`

Exit criteria:
- workflow nodes no longer depend on the custom capability registry for platform calls;
- domain compute functions remain in the application layer and operate on already-fetched results;
- the agent path uses the same foundation APIs the diagram describes.

### Phase 4: Retire custom capability plumbing and complete the target boundary

Goal: remove hard-coded tool orchestration from the application once the new capability layer is stable.

Changes:
- Retire `AnalyticsFoundation/capability_registry.py` for workflow-side capability routing once all agent flows use MCP.
- Keep the BFF direct display route independent of the agentic flow.
- Add Kafka and Hive MCP wrappers as boundary placeholders without wire-in to the OPO workflow.
- Keep the model gateway and session/audit/memory services in the foundation layer.

Exit criteria:
- the repo matches the target component layout in the architecture diagram;
- the application no longer owns runtime-level capability plumbing;
- the system is ready for later production integration with real deployed Analytics Foundation APIs.

## Sequencing and dependency order

1. `application_agent/` package and model abstraction
2. PostgreSQL runtime-state migration
3. MCP adaptor layer and workflow node updates
4. retirement of custom registry path and boundary completion

This order minimizes risk: the application agent and database changes are easier to validate first, then the workflow is re-pointed to the MCP capability layer.

## What does not change in this migration

- OPO domain logic remains in `ApplicationUI/analytics_agents/opo_monitoring_service/services.py`.
- The static UI and the direct BFF trend route remain operational.
- The investigation lifecycle stays the same: parse scope -> detect outliers -> human gate -> register -> deep dive -> summarize.
- The application retains ownership of business meaning and evidence interpretation.

## Open decisions before implementation

- Local dev transport for MCP: stdio vs. streamable HTTP.
- Which `services.py` functions are fetch-oriented versus compute-oriented.
- Whether PostgreSQL for dev is run through docker-compose or via a shared pre-existing instance.
- Whether the Kafka/Hive MCP servers remain stubs for now or are prepared for future tool definitions.

## Implementation recommendation

Proceed incrementally in the order above, with each phase being independently testable. This preserves current application behavior while moving toward the target architecture without forcing a large-bang rewrite.

## Execution backlog

### Phase 1 — application agent layer

- [ ] Define the application agent package structure under `ApplicationUI/analytics_agents/opo_monitoring_service/application_agent/`.
- [ ] Create `agents.py` with `Agent[DetectionScope]` and `Agent[FindingsSummary]` definitions.
- [ ] Move prompt and structured-output logic out of `application_workflow.py` and into the agent definitions.
- [ ] Refactor `AnalyticsFoundation/model_gateway.py` into a PydanticAI model factory without OPO-specific business semantics.
- [ ] Validate that the same user workflow still parses scope and summarises findings with equivalent output types.

### Phase 2 — PostgreSQL runtime state

- [ ] Add a local Postgres config and initialization scripts for dev/test.
- [ ] Replace `SqliteSaver` with `PostgresSaver` in the graph setup.
- [ ] Add `sessions`, `agent_session_events`, `workspace_registrations`, and `memory` tables.
- [ ] Migrate current session-memory writes to the new PostgreSQL-backed store.
- [ ] Verify graph resume and evidence persistence across restart boundaries.

### Phase 3 — MCP capability layer

- [ ] Create an MCP server for StarRocks-backed queries using the existing `lanadb_query.py` / `datawarehouse.py` logic as the back-end contract.
- [ ] Create an MCP server for Analytics Foundation APIs using `workspace_client.py`, `query_engine_client.py`, `processing_client.py`, and `assets_client.py`.
- [ ] Add Kafka MCP and Hive MCP stub servers as non-wired placeholders matching the target diagram.
- [ ] Update workflow nodes to call MCP tools instead of custom capability registry calls.
- [ ] Split fetch-oriented and compute-oriented responsibilities in `services.py` so domain logic remains application-owned and API access is delegated to the adaptor layer.
- [ ] Keep `interrupt()` gates in front of sensitive tool actions such as registration and bulk dataset operations.
- [ ] Verify the workflow still executes the same investigation path with MCP-backed operations.

### Phase 4 — retire compatibility plumbing

- [ ] Retire `AnalyticsFoundation/capability_registry.py` from the workflow path once MCP is the active tool contract.
- [ ] Keep direct BFF trend endpoints operating independently of the agentic workflow.
- [ ] Confirm the repo visually matches the target architecture and no custom runtime plumbing remains in the app layer.
- [ ] Document the final boundary: application semantics, foundation runtime, and service APIs.

## Suggested implementation order

1. Phase 1: agent layer and model contract
2. Phase 2: PostgreSQL migration for checkpoints and session evidence
3. Phase 3: MCP wiring and workflow re-targeting
4. Phase 4: cleanup and final boundary alignment

This order keeps each stage independently verifiable and avoids a risky all-at-once rewrite.

