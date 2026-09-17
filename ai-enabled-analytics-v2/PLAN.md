# ai-enabled-analytics-v2 — Build Plan

## Purpose

`ai-enabled-analytics-v2` is a **new, additive** implementation of the target
architecture in
[`../agentWorkflows/mcp-oss-target-architecture.puml`](../agentWorkflows/mcp-oss-target-architecture.puml),
built alongside the existing demonstrator (`AnalyticsFoundation/`, `ApplicationUI/`)
without editing, deleting, or otherwise disturbing it. The existing services keep
running exactly as they do today; this folder is where the OSS-aligned target
boundary is implemented and validated.

This plan follows the phases already agreed in
[`../agentWorkflows/mcp-oss-migration-plan.md`](../agentWorkflows/mcp-oss-migration-plan.md),
re-scoped to "build fresh under `v2/`" instead of "refactor in place".

## Non-negotiable constraints

- No file under `AnalyticsFoundation/`, `ApplicationUI/`, `apis/`, or the repo root
  is modified, moved, or deleted by this work.
- Business semantics (KPI definitions, outlier rules, investigation workflow) stay
  application-owned and are **ported**, not reinvented — behavior must remain
  equivalent to the current demonstrator.
- Analytics Foundation owns: model gateway, session/audit persistence, capability
  governance, and platform API integration — mirrored here under `foundation/`.
- MCP is the only path from the agent runtime to Foundation APIs.
- PostgreSQL is the single runtime-state store (checkpoints + session/audit/memory).
- Where v2 needs the same mock datasets as the original (`AnalyticsFoundation/mock_data/*`)
  or the same static UI assets (`ApplicationUI/opo_monitoring_ui/static/*`), it
  **reads them in place** (read-only path reference) rather than copying/forking
  them, so there is a single source of truth and nothing under the original tree
  is touched.

## Language boundary (Java + Python)

Per `.github/copilot-instructions.md` `### 2.1 Language boundary`, this is a
two-language target, not a Python-only one:

- **Python owns the workflow runtime only**: `agent_runtime/` (LangGraph +
  PydanticAI application agent), `mcp_capability_adaptor/`, and `foundation/`
  (model gateway, session manager, checkpointer, platform clients). Python has
  no app-facing HTTP surface in the target state — the current
  `application_ui/opo_monitoring_service/api.py` FastAPI BFF is an **interim**
  stand-in for local validation only, and is replaced by the Java façade in
  Phase 5 below.
- **Java owns the app and API façade**: UI shell, BFF/REST layer, and the
  stable service interfaces in `.github/copilot-instructions.md` `## 8`
  (`TrendService`, `WorkspaceService`, `RegistrationService`,
  `WaferDataService`). Java never calls the model gateway, MCP tools, or
  PostgreSQL/StarRocks directly; it calls the Python workflow runtime's own
  HTTP API (the same routes `api.py` exposes today: invoke/resume/thread-state/
  trends/session-events), using the shared contracts below.
- **Shared contracts** are the only thing both languages depend on for model,
  session, and foundation access — neither side redefines the other's types by
  hand. See `contracts/` below.

## Target component mapping

| Target architecture component | v2 location | Language |
|---|---|---|
| Application UI / BFF | `app-ui-service/` (Phase 5) — deployed; `application_ui/opo_monitoring_service/api.py` is now the Python workflow runtime's own API it calls | Java (target) / Python (workflow runtime) |
| Agent Runtime Framework (LangGraph + PydanticAI agent) | `agent_runtime/graph.py`, `agent_runtime/application_agent/` | Python |
| MCP Capability Adaptor | `mcp_capability_adaptor/` (StarRocks, Analytics API, Kafka stub, Hive stub servers + client) | Python |
| Model Gateway | `foundation/model_gateway.py` | Python |
| Session Manager | `foundation/session_manager.py` (PostgreSQL-backed) | Python |
| Foundation Service APIs (Assets/Workspace/Query/Processing) | `foundation/clients/*.py` (implementation behind the MCP adaptor) | Python |
| PostgreSQL runtime state (checkpoints + sessions/audit/evidence) | `db/schema.sql`, `foundation/postgres_checkpointer.py`, `docker-compose.yml` | Python-managed |
| Shared contracts | `contracts/` (Phase 5) — JSON Schema generated from `agent_runtime/application_agent/contracts.py` plus an OpenAPI spec for the workflow runtime's own API | Both (generated) |

## Phased execution

### Phase 1 — Application agent layer
- Define `DetectionScope` / `FindingsSummary` contracts in
  `agent_runtime/application_agent/contracts.py` (ported from
  `application_workflow.py`, unchanged field semantics).
- Define `pydantic_ai.Agent` instances in `agent_runtime/application_agent/agents.py`
  for scope parsing and findings summarization, replacing the raw
  `llm.with_structured_output(...)` calls.
- `foundation/model_gateway.py` exposes a PydanticAI-compatible model factory only
  (no OPO-specific prompts or business semantics).
- `agent_runtime/graph.py` is the orchestration wrapper (mirrors
  `application_workflow.py`'s node graph: parse scope → confirm threshold →
  analyze trends → confirm investigation → register → deep dive → summarize),
  calling into the application agent layer and MCP tools instead of the model
  client and capability registry directly.

### Phase 2 — PostgreSQL runtime state
- `db/schema.sql` defines `sessions`, `agent_session_events`,
  `workspace_registrations`, and `memory` tables, plus the LangGraph checkpoint
  tables (created by `langgraph.checkpoint.postgres.PostgresSaver.setup()`).
- `foundation/postgres_checkpointer.py` builds a `PostgresSaver` from
  `DATABASE_URL` for `agent_runtime/graph.py` to compile the graph with.
- `foundation/session_manager.py` re-implements `session_memory.py`'s public
  surface (`configure_store`, `record_event`, `timed_event`, `set_session_id`,
  `current_session_id`, `get_store().list_events`) against PostgreSQL instead of
  per-project SQLite, so callers do not need to change shape.
- `docker-compose.yml` provides a local Postgres instance for dev/test.

### Phase 3 — MCP capability layer
- `mcp_capability_adaptor/server_starrocks.py`: MCP server wrapping
  `foundation/clients/lanadb_query.py` and `datawarehouse.py` (trend + wafer reads).
- `mcp_capability_adaptor/server_analytics_api.py`: MCP server wrapping
  `foundation/clients/workspace_client.py`, `query_engine_client.py`,
  `processing_client.py`, `assets_client.py` (workspace lifecycle, dataset
  registration, connection info, processing instances, assets).
- `mcp_capability_adaptor/server_kafka_stub.py` / `server_hive_stub.py`: boundary
  placeholders matching the target diagram, not wired into the OPO workflow.
- `mcp_capability_adaptor/client.py`: thin in-process MCP client used by
  `application_ui/opo_monitoring_service/services.py` and `agent_runtime/graph.py`
  to call tools instead of `AnalyticsFoundation.capability_registry.invoke(...)`.
- `application_ui/opo_monitoring_service/services.py` keeps pure domain
  computation (`analyse_series`, `get_kpi_threshold_context`, wafer scoring) and
  delegates all data access to the MCP client.
- `interrupt()` human-approval gates are preserved in `agent_runtime/graph.py`
  ahead of registration and bulk dataset operations, same as today.

### Phase 4 — Boundary completion
- No custom capability-registry equivalent is used from the workflow path in v2;
  MCP is the only tool-call path from day one (v2 does not need a "retire" step
  because it is built directly on the target shape).
- `application_ui/opo_monitoring_service/api.py` keeps the direct `/trends`
  display route independent of the agent path (`services.get_trend_series()` via
  MCP, no LangGraph/model involvement), matching the diagram's
  `bff ..> query_api : GET /trends, no agent or MCP` intent as closely as the
  mocked Foundation APIs allow.
- Once validated, this tree becomes the reference implementation the original
  demonstrator can be cut over to; no action is taken on the original tree as
  part of this plan.

### Phase 5 — Java app/API façade and shared contracts

Goal: move the app-facing HTTP surface to Java per the language boundary, with
the Python side reduced to the workflow runtime's own API.

Changes:
- Add `contracts/` at the `ai-enabled-analytics-v2` root:
  - `contracts/model/` — JSON Schema for `DetectionScope` and `FindingsSummary`,
    generated from `agent_runtime/application_agent/contracts.py`
    (`BaseModel.model_json_schema()`), checked in rather than generated ad hoc.
  - `contracts/workflow-runtime-api/openapi.yaml` — the Python workflow runtime's
    own HTTP API (invoke/resume/thread-state/trends/session-events), which is
    what the Java façade calls. This is a **new, narrower** contract than
    Foundation's internal MCP tool schemas; Java never sees those.
  - `contracts/session/` — JSON Schema for the `agent_session_events` /
    `workspace_registrations` / `memory` row shapes returned by the session
    endpoints.
- Keep `application_ui/opo_monitoring_service/api.py` as the **Python workflow
  runtime's own API** (still FastAPI, still calling `agent_runtime.graph`
  directly). Beyond the original `/chat`/`/resume`/`/trends`/`/threads/{id}`/
  `/sessions/{id}/events` routes, it now also exposes direct (non-agentic)
  `POST /workspaces`, `POST /workspaces/{id}/filters`,
  `POST /workspaces/{id}/register`, and `POST /workspaces/{id}/wafers/query`
  routes so the Java façade's `WorkspaceService` / `RegistrationService` /
  `WaferDataService` have something concrete to call for the traditional
  (non-conversational) deep-dive path, without Java ever reaching MCP/Foundation
  itself. It stops being "the BFF" and becomes the thing the Java façade calls,
  matching the language boundary's "Python has no app-facing HTTP surface" rule
  only once Java is in front of it.
- Add `app-ui-service/` (new Maven/Gradle module) implementing the `## 8` Java
  service interfaces (`TrendService`, `WorkspaceService`, `RegistrationService`,
  `WaferDataService`) plus the conversational routes (`/chat`, `/resume`,
  `/threads/{id}`), generating its DTOs from `contracts/` instead of hand-written
  POJOs, and calling the Python workflow runtime's API instead of implementing
  any of this logic itself.
- Serve the static UI from the Java façade (or keep serving it from Python only
  as a fallback during migration); do not fork the UI assets.

Exit criteria:
- The Java façade is the only thing the browser/app talks to.
- The Python workflow runtime's API surface matches `contracts/workflow-runtime-api/openapi.yaml`
  exactly; no field is added on one side without the contract being updated first.
- Java has zero imports of/calls to model providers, MCP, or PostgreSQL/StarRocks.

## Execution backlog

- [x] `foundation/config.py` — settings (model gateway, DB URL, MCP transport)
- [x] `foundation/model_gateway.py` — PydanticAI model factory
- [x] `foundation/postgres_checkpointer.py` — `PostgresSaver` builder
- [x] `foundation/session_manager.py` — Postgres-backed session/event store
- [x] `foundation/clients/*.py` — workspace/query/processing/assets/lanadb/datawarehouse clients (ported)
- [x] `db/schema.sql` — sessions/events/registrations/memory tables
- [x] `docker-compose.yml` — local Postgres for dev
- [x] `mcp_capability_adaptor/server_starrocks.py` — trend/wafer read tools
- [x] `mcp_capability_adaptor/server_analytics_api.py` — workspace/query/processing/assets tools
- [x] `mcp_capability_adaptor/server_kafka_stub.py`, `server_hive_stub.py` — placeholders
- [x] `mcp_capability_adaptor/client.py` — in-process MCP client
- [x] `agent_runtime/application_agent/contracts.py` — `DetectionScope`, `FindingsSummary`
- [x] `agent_runtime/application_agent/agents.py` — `Agent[DetectionScope]`, `Agent[FindingsSummary]`
- [x] `agent_runtime/graph.py` — LangGraph `StateGraph`, `PostgresSaver`, MCP-backed nodes
- [x] `application_ui/opo_monitoring_service/services.py` — domain compute only
- [x] `application_ui/opo_monitoring_service/api.py` — Python workflow runtime API (`/chat`, `/resume`, `/trends`, `/sessions/{id}/events`, `/threads/{id}`, `/workspaces*`)
- [x] `run.sh` — start/stop/status for the v2 stack on its own port
- [x] `requirements.txt`, `.env.example` — v2 dependencies and config template
- [x] `contracts/model/*.schema.json` — generated `DetectionScope` / `FindingsSummary` JSON Schema (`contracts/generate_model_schemas.py`)
- [x] `contracts/workflow-runtime-api/openapi.yaml` — Python workflow runtime API contract
- [x] `contracts/session/*.schema.json` — session/event/evidence row shapes
- [x] `app-ui-service/` — Spring Boot module implementing `## 8` interfaces + conversational routes; DTOs hand-written to match `contracts/` today (codegen wiring is a follow-up, see `app-ui-service/README.md`), calling the Python workflow runtime API only. Compiles and its Spring context loads (`mvn test`).
- [x] `Dockerfile` (repo root context, workflow runtime), `app-ui-service/Dockerfile` — both build locally (`docker build .`)
- [x] `deploy/build-and-ship-*.sh`, `deploy/k8s/*.yaml`, `deploy/README.md` — image build/ship/apply pattern
- [x] `deploy/k8s/ingress-app-ui-service.yaml`, `deploy/k8s/ingress-app-ui.yaml` — Istio `VirtualService` exposure through the shared cluster ingress gateway (replaces `kubectl port-forward` for real testing)

### Phase 6 — Containerize and deploy to `ai-agents`

Goal: ship the three runtime pieces (PostgreSQL, Python workflow runtime, Java
facade) to the cluster, following the repo's standard image pattern
(`.github/copilot-instructions.md` `## 9 Deployment`) rather than inventing a
new one:

```bash
mvn clean package
docker build -t <image> .
docker save -o <image>.tar <image>
scp <image>.tar fa-VCP@ics027036188.ics-eu-1.asml.com:/home/fa-VCP/
```

Confirmed against the real cluster (SSH bastion `fa-VCP@ics027036188.ics-eu-1.asml.com`):
the bastion has `podman`, not `docker`, and nodes run containerd (RKE2); images
are made available to the cluster by pushing to the internal registry
`repo.cluster.local:5443` after `scp`, i.e.:

```bash
ssh fa-VCP@... "podman load -i <image>.tar && \
  podman tag <local-image> repo.cluster.local:5443/ai-agents/<name>:<tag> && \
  podman push repo.cluster.local:5443/ai-agents/<name>:<tag>"
```

`deploy/build-and-ship-*.sh` automate the whole local-build → scp →
load/tag/push chain per image. `deploy/k8s/*.yaml` reference the
`repo.cluster.local:5443/ai-agents/...` images with `imagePullPolicy: Always`
(required — nodes cache the `latest` tag by digest, so `IfNotPresent` silently
keeps serving a stale image after a re-push under the same tag).

`deploy/k8s/postgres.yaml`, `workflow-runtime.yaml`, `app-ui-service.yaml` are
applied, in that order, into the `ai-agents` namespace, via the SSH host per
the existing repo convention:

```bash
ssh fa-VCP@ics027036188.ics-eu-1.asml.com kubectl apply -n ai-agents -f - < deploy/k8s/postgres.yaml
```

See `deploy/README.md` for the full walkthrough, including the secrets/config
(`db/schema.sql` as a ConfigMap, Postgres password, DB URL) created out-of-band
before applying `workflow-runtime.yaml`.

Exit criteria:
- All three images build and load on the cluster host. **Met.**
- `app-ui-service` Service is the only one exposed to the app/UI; `GET
  /trends` through it behaves the same as hitting `analytics-workflow-runtime`
  directly. **Met** (verified via `kubectl exec ... curl`, see below).
- Model gateway auth works from inside the cluster. **Not met** — see below.

**Status: deployed and running in the `ai-agents` namespace on the real
cluster**, after fixing four issues only found by actually deploying (i.e. not
caught by local `mvn test` / `docker build`):

1. **`mcp>=1.6` resolved to `mcp` 2.x** in the container, which renamed
   `FastMCP` (removing `mcp.server.fastmcp`); `mcp_capability_adaptor/server_*.py`
   uses the 1.x API. Fixed by pinning `mcp>=1.6,<2` in `requirements.txt`.
2. **Blocking Key Vault/IMDS credential probe on startup.** `DefaultAzureCredential`
   attempting `ManagedIdentityCredential` via IMDS hangs indefinitely (many
   minutes, never timing out) on this on-prem cluster with no reachable Azure
   endpoint or configured identity - this blocked the whole ASGI app from
   finishing startup (`/trends` unreachable) even though the call was inside a
   `try/except`. Fixed in `application_ui/opo_monitoring_service/api.py` by
   moving the model-client warm-up to a background daemon thread, so a slow or
   hanging Key Vault call can no longer block startup or any request; `/chat`
   would still hang on its own request today if invoked (see item below).
3. **Node-level image cache with a reused `latest` tag.** After fixing the
   `mcp` pin and re-pushing to the same `repo.cluster.local:5443/.../latest`
   tag, the node still ran the old (pre-fix) image content because
   `imagePullPolicy: IfNotPresent` doesn't compare digests for a tag it already
   has cached. Fixed by switching both app images to `imagePullPolicy: Always`.
4. **Jackson camelCase vs. Python snake_case field mismatch** in `app-ui-service`:
   `TrendSeries`/etc. DTOs use camelCase (`lotId`, `kpiValue`) while the Python
   API's JSON is snake_case (`lot_id`, `kpi_value`), so proxied fields came
   through as `null`/`0.0`. Fixed globally via
   `spring.jackson.property-naming-strategy: SNAKE_CASE` in
   `app-ui-service/src/main/resources/application.yml` instead of annotating
   every DTO field.
5. `deploy/k8s/postgres.yaml` also needed `storageClassName: longhorn` (no
   default StorageClass on this cluster → PVC stuck `Pending`), a pod-level
   `fsGroup: 999`, and `PGDATA=/var/lib/postgresql/data/pgdata` (Longhorn PVCs
   mount with a `lost+found` dir at the root, which trips `initdb` if `PGDATA`
   points at the mount root directly).

**Still open / not fixed:** Key Vault auth itself (item 2) means the actual
model-backed `/chat` investigation flow has not been verified in-cluster - only
`/trends` (no agent/model involved) was. The workflow runtime needs a real
managed/workload identity bound to its pod, or an alternative credential
source, before `/chat` can work there; until then, expect that route to hang
per-request (not crash the pod) if called. `deploy/k8s/*.yaml` were not
hardened against this cluster's `restricted` Pod Security admission (all three
apply with a non-blocking `Warning`, not an error, about
`allowPrivilegeEscalation`/`capabilities`/`runAsNonRoot`/`seccompProfile` -
left as-is since it only warns today, but should be tightened before this is
treated as a long-lived deployment).

### Post-deployment fixes (found via real browser testing through a port-forward)

Testing the UI from a local browser (`ssh -L 8090:localhost:8090 -L
8100:localhost:8100 ... "kubectl port-forward ..."`) surfaced two more bugs
that `GET /trends` alone didn't exercise:

6. **`POST /chat` returned HTTP 500 on the very first click.** Root cause:
   `foundation/postgres_checkpointer.py` built `PostgresSaver` from
   `PostgresSaver.from_conn_string(...)`, a single bare `psycopg` connection
   entered once at startup and never re-established. That connection went
   stale in-cluster (`psycopg.OperationalError: the connection is closed`)
   before the checkpointer ever loaded a checkpoint tuple - i.e. before the
   graph even ran. Fixed by switching to a `psycopg_pool.ConnectionPool`
   (`PostgresSaver(pool)`), which transparently opens a fresh connection per
   operation instead of reusing one until it dies. `agent_runtime/graph.py`
   updated to call `build_checkpointer()` directly (no more manual
   `__enter__()`). `requirements.txt` now pins `psycopg[binary,pool]`.
7. **Fixing #6 exposed the previously-undiscovered consequence of item 2**:
   with the DB working, `parse_scope` reached its actual model call, which
   hung on the Key Vault/IMDS probe exactly as documented - except now inside
   a live HTTP request, so the browser just spun forever. Fixed with a hard
   10s timeout around the Key Vault fetch in `foundation/config.py::get_api_key`
   (`concurrent.futures` + a **module-level, never-shut-down**
   `ThreadPoolExecutor`). The first attempt at this fix used
   `with ThreadPoolExecutor(...) as executor:`, which looked correct but
   doesn't work: exiting a `with`-managed executor calls
   `shutdown(wait=True)`, which blocks until the (still-hung) submitted work
   finishes - silently defeating the whole `future.result(timeout=...)` call.
   Verified fixed: `POST /chat` with "show me trends and outliers" now returns
   an `awaiting_human` response with real P95/P99 evidence in ~10s (the
   Key Vault timeout firing, then `parse_scope` falling back to defaults, per
   the existing `except Exception:` handler) instead of a 500 or a hang.

**Rename note:** the Java module/Deployment/Service/image were originally
named `analytics-facade` (matching `apis/api.yml`'s pre-existing "Analytics
Facade REST API" naming), then renamed to `app-ui-service` for clarity. The
old `analytics-facade` Deployment/Service were deleted and recreated as
`app-ui-service` in the live `ai-agents` namespace (re-verified `GET /trends`
afterward); the old `repo.cluster.local:5443/ai-agents/analytics-facade:latest`
image tag was left in the registry (not deleted - registry delete wasn't
attempted) and is now stale/unused.

### Ingress exposure (replacing `kubectl port-forward`)

`kubectl port-forward` proved unreliable for real testing (drops under load /
after ~30-60s idle: `error creating error stream ...: Timeout occurred`,
`broken pipe`). This cluster has a real shared Istio ingress `Gateway`
(`istio-system/ingress-prod`) running on edge-labeled nodes
(`asml.com/vcp-node-type=k8s_edge`, e.g. `ics027032213`), reachable at
`http://ics027032213.ics-eu-1.asml.com:8080` (port **8080** is the gateway
pods' actual `hostPort`, not 80 - the in-cluster Service's port 80 is
ClusterIP-only). Every other app on this cluster shares that one wildcard-host
Gateway and disambiguates by URL path prefix via its own `VirtualService`
(confirmed by inspecting existing ones, e.g.
`analytics-fnd-gateway-prod/vcp-ingress-prod-foundation-framework-api-gateway-service`).

Added, mirroring that convention:
- `deploy/k8s/ingress-app-ui-service.yaml` — `app-ui-service` under `/ai`
  (prefix stripped via `uriRegexRewrite`). Verified: `GET /ai/trends` → 200.
- `deploy/k8s/ingress-app-ui.yaml` — the browser UI under `/ai-ui`, **plus**
  bare-path routes for `/trends`, `/chat`, `/resume`, `/threads/*`,
  `/sessions/*`, `/static/*`, `/vendor/*`, because
  `ApplicationUI/opo_monitoring_ui/static/app.js` (off-limits) calls all of
  those as absolute root paths with no concept of a path prefix. Verified:
  full page load + trend chart render with zero console errors at
  `http://ics027032213.ics-eu-1.asml.com:8080/ai-ui/`.

**This second one is an interim/test convenience, not a long-term exposure**:
those bare paths are fairly generic names on a *multi-tenant* shared gateway;
a collision check (`kubectl get virtualservice -A`, no other VS claims any of
them today) was only done once, at the time of writing. The target state
remains app-ui-service serving the UI itself behind its own `/ai` prefix with
no absolute-path assumptions (see Phase 6 exit criteria above, still open).

## Verification approach

1. `docker compose up -d` to start local Postgres, then apply `db/schema.sql`.
2. `./run.sh start` to launch the v2 FastAPI/uvicorn service on a distinct port
   from the original (`ASML_AI_V2_PORT`, default `8100`).
3. `GET /trends` returns the same shape as the original demonstrator.
4. `POST /chat` with a baseline-mode question reaches the same
   `awaiting_human` / `no_outliers` / `complete` shapes as today, evidenced via
   `GET /sessions/{id}/events` reading from PostgreSQL instead of SQLite.
5. Restart the process mid-investigation and confirm `GET /threads/{id}` resumes
   from the `PostgresSaver` checkpoint.
6. `cd app-ui-service && mvn -q test` — confirmed passing (Spring context
   loads against the parent POM resolved from Maven Central; Java 8 / Spring
   Boot 2.7.18, `mvn spring-boot:run` serves the facade on `:8090`).
7. With both services running, `GET :8090/trends` and `GET :8100/trends`
   return the same (correctly field-mapped) data — **confirmed in-cluster** via
   `kubectl exec deploy/app-ui-service -- curl 127.0.0.1:8090/trends` against
   the real `ai-agents` deployment. `POST /chat` end-to-end is not yet
   confirmed (blocked on Key Vault/model-gateway auth in-cluster, see Phase 6).
8. `docker build` for both `Dockerfile` (repo root) and `app-ui-service/Dockerfile`
   — confirmed passing. `deploy/build-and-ship-*.sh` and
   `kubectl apply -n ai-agents` — **run against the real cluster**; all three
   pods (`analytics-postgres`, `analytics-workflow-runtime`, `app-ui-service`)
   are `1/1 Running` with 0 restarts. See Phase 6 for the issues found and fixed
   along the way.

## Open decisions (carried over, still open in v2)

- Local dev MCP transport: stdio vs. streamable HTTP (v2 ships both server
  modules ready for either; default wiring uses in-process/stdio for simplicity).
- Whether Postgres for dev is docker-compose (default here) or a shared instance.
- Kafka/Hive MCP servers remain stubs until a real integration is scoped.
- Contract generation direction: hand-author `contracts/` and generate both
  Pydantic and Java types from it, vs. generate `contracts/` from the Python
  models and treat Java as the consumer only (leaning toward the latter, since
  `DetectionScope`/`FindingsSummary` are Python/PydanticAI-owned today).
- Java web framework and build tool for `app-ui-service/`. **Resolved**:
  Spring Boot 2.7.18 / Maven, Java 8 (matches this machine's available JDK).
- How the workflow runtime authenticates to Key Vault once in-cluster
  (confirmed blocking issue, not just theoretical: `DefaultAzureCredential`'s
  `ManagedIdentityCredential`/IMDS probe hangs indefinitely with no configured
  identity on this cluster — see `deploy/k8s/workflow-runtime.yaml` and Phase 6).
- Whether the `ai-agents` cluster can pull images from a registry directly, or
  every image must go through the save/scp/load path in `deploy/`. **Resolved
  for this cluster**: push to the internal `repo.cluster.local:5443` registry
  via `podman` on the bastion (no docker there; nodes run containerd/RKE2).
- Hardening `deploy/k8s/*.yaml` against this cluster's `restricted` Pod
  Security admission (`allowPrivilegeEscalation: false`, dropped capabilities,
  `runAsNonRoot: true`, `seccompProfile`) — currently only warns, not enforced,
  but should be fixed before this is a long-lived deployment.
