# app-ui-service

App/API facade (PLAN.md Phase 5). Owns the app-facing HTTP surface; never calls
the model gateway, MCP tools, or PostgreSQL/StarRocks directly — everything goes
through `WorkflowRuntimeClient`, which talks only to the Python workflow
runtime's own API described in
[`../contracts/workflow-runtime-api/openapi.yaml`](../contracts/workflow-runtime-api/openapi.yaml).

## Layout

```
config/      WorkflowRuntimeProperties (base URL), RestTemplate bean
client/      WorkflowRuntimeClient - the one HTTP path to the Python service
dto/         Request/response types mirroring ../contracts/*
service/     TrendService, WorkspaceService, RegistrationService, WaferDataService
             (exact interfaces from .github/copilot-instructions.md `## 8`) + impls
controller/  REST endpoints the app/UI calls
```

## Run locally

```bash
# 1. Start the Python workflow runtime first (see ../README.md)
cd ai-enabled-analytics-v2
./run.sh start                      # serves on :8100

# 2. Start the facade
cd app-ui-service
mvn spring-boot:run                 # serves on :8090
```

`workflow-runtime.base-url` in `src/main/resources/application.yml` points at
the Python service; override with `WORKFLOWRUNTIME_BASEURL` or
`-Dworkflow-runtime.base-url=...` if it runs elsewhere.

## DTOs are hand-written, not yet generated

The classes under `dto/` are hand-written to match `../contracts/` today. Per
PLAN.md Phase 5's open decision, wire in a generator instead of maintaining
these by hand once the contracts stabilize, e.g.:

- `openapi-generator-maven-plugin` against `../contracts/workflow-runtime-api/openapi.yaml`
  for `ChatRequest`, `ResumeRequest`, `InvestigationResponse`, `ThreadState`, `TrendResponse`.
- `jsonschema2pojo-maven-plugin` against `../contracts/model/*.schema.json` and
  `../contracts/session/*.schema.json` for `DetectionScope`, `FindingsSummary`,
  and the session event/registration/memory row types.

Until that plugin is wired in, keep any field added on the Python side in sync
with both the relevant file under `../contracts/` and its DTO here.
