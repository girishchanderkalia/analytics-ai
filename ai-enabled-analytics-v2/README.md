# ai-enabled-analytics-v2

Target-architecture implementation of the Analytics Investigation Agent, built
**alongside** the original demonstrator (`../AnalyticsFoundation`,
`../ApplicationUI`) without modifying it. See [PLAN.md](PLAN.md) for the full
phased plan and the mapping from
[`../agentWorkflows/mcp-oss-target-architecture.puml`](../agentWorkflows/mcp-oss-target-architecture.puml)
to this folder's structure.

## Layout

```
foundation/                  # Model gateway, PostgreSQL session/audit store, checkpointer, platform clients
mcp_capability_adaptor/      # MCP servers (StarRocks, Analytics API, Kafka/Hive stubs) + in-process client
agent_runtime/               # LangGraph workflow + PydanticAI application agents (DetectionScope, FindingsSummary)
application_ui/              # Python workflow runtime's own FastAPI service + OPO domain logic (services.py is compute-only)
app-ui-service/              # Java app/API facade (Spring Boot) - the only thing the app/UI talks to
contracts/                   # Shared model/session/workflow-runtime-API contracts consumed by both sides
db/schema.sql                # sessions / agent_session_events / workspace_registrations / memory tables
docker-compose.yml           # local PostgreSQL for dev
```

## Local setup

```bash
cd ai-enabled-analytics-v2
docker compose up -d           # starts PostgreSQL and applies db/schema.sql
cp .env.example .env           # fill in values, especially ASML_AI_KEY_VAULT_URL access
./run.sh start                 # installs deps into .venv and starts the Python workflow runtime on :8100
cd app-ui-service && mvn spring-boot:run   # starts the Java facade on :8090
```

`GET /trends` (via either `:8100` directly or `:8090` through the facade)
returns the same shape as the original demonstrator's `/trends`. `POST /chat`
drives the same investigation flow (parse scope → human threshold
clarification if needed → analyze trends → confirm investigation → create
workspace → apply filters → approve registration → register and wait → query
wafers → summarize), now backed by MCP tool calls and a PostgreSQL
checkpointer/session store instead of direct client imports and SQLite.

## What is intentionally unchanged from the original demonstrator

- OPO business semantics: outlier detection rules, KPI interpretation, the
  investigation lifecycle, and the human-approval gates.
- The static UI (`ApplicationUI/opo_monitoring_ui/static`), referenced in place.
- The mocked platform datasets (`AnalyticsFoundation/mock_data/*`), referenced
  in place, read-only.

## What is new here, per the target architecture

- MCP is the only path from the workflow/services to platform data — no module
  under `application_ui/` or `agent_runtime/` imports a platform client
  directly; everything goes through `mcp_capability_adaptor.client`.
- PydanticAI `Agent[DetectionScope]` / `Agent[FindingsSummary]` replace raw
  `with_structured_output` calls.
- PostgreSQL (`langgraph.checkpoint.postgres.PostgresSaver` + `db/schema.sql`)
  replaces per-project SQLite for both checkpoints and session/audit events.

## Language boundary (Java + Python)

Per `.github/copilot-instructions.md` `### 2.1 Language boundary`: Python owns
the workflow runtime only (`foundation/`, `mcp_capability_adaptor/`,
`agent_runtime/`, and `application_ui/`'s FastAPI service). Java owns the
app/API façade: `app-ui-service/` implements the `## 8` service interfaces
(`TrendService`, `WorkspaceService`, `RegistrationService`, `WaferDataService`)
plus the conversational routes, and never calls the model gateway, MCP, or
PostgreSQL/StarRocks directly — only the Python service's own HTTP API. Both
sides are kept in sync against the checked-in `contracts/` folder (model,
session, and workflow-runtime-API schemas) instead of hand-written types
diverging on either side. See PLAN.md "Phase 5" for the full plan and
remaining follow-ups (contract-driven codegen for the Java DTOs, static UI
served from the façade).

## Deployment (Phase 6)

`Dockerfile` (repo root context) and `app-ui-service/Dockerfile` package the
workflow runtime and facade; `deploy/` has the build/ship scripts and
`ai-agents`-namespace Kubernetes manifests, following the repo's standard
image pattern (`.github/copilot-instructions.md` `## 9 Deployment`):
`mvn clean package` → `docker build` → `docker save` → `scp` to the cluster
host → `podman load`/`tag`/`push` to the internal `repo.cluster.local:5443`
registry there → `kubectl apply -n ai-agents`. See
[`deploy/README.md`](deploy/README.md).

**Deployed and running** in the real `ai-agents` namespace: all three pods
(`analytics-postgres`, `analytics-workflow-runtime`, `app-ui-service`) are
`1/1 Running`, and `GET /trends` was verified end-to-end through the facade.
Getting there surfaced and fixed four real bugs (an `mcp` 2.x incompatibility,
a Key Vault call blocking startup indefinitely, a stale node image cache, and
a Jackson field-naming mismatch) — see PLAN.md "Phase 6" for details. **Still
open:** the workflow runtime can't yet authenticate to Key Vault in-cluster
(no managed/workload identity configured), so the model-backed `/chat` flow
isn't verified there yet; and contract-driven codegen for the Java DTOs (see
`app-ui-service/README.md`) is still a follow-up.
