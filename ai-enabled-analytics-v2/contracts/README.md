# Shared contracts

Per `.github/copilot-instructions.md` `### 3.5 Shared contracts`: model, session,
and foundation-access shapes are defined once here and consumed by both the
Python workflow runtime and the Java app/API facade, instead of being
hand-written twice.

- `model/` — JSON Schema for `DetectionScope` / `FindingsSummary`, generated
  from `agent_runtime/application_agent/contracts.py` by
  `generate_model_schemas.py`. **Do not hand-edit**; re-run the generator after
  changing the Python models.
- `workflow-runtime-api/openapi.yaml` — the Python workflow runtime's own HTTP
  API (`/chat`, `/resume`, `/threads/{id}`, `/trends`, `/sessions/{id}/events`,
  `/capabilities`), hand-authored and kept in sync with
  `application_ui/opo_monitoring_service/api.py`. This is what the Java facade
  calls; it is narrower than, and does not expose, Foundation's internal MCP
  tool schemas.
- `session/` — JSON Schema for the `agent_session_events` /
  `workspace_registrations` / `memory` row shapes (`db/schema.sql`,
  `foundation/session_manager.py`).

## Regenerating

```bash
cd ai-enabled-analytics-v2
python contracts/generate_model_schemas.py
```

## Consuming from Java

`app-ui-service/` does not hand-write DTOs for these shapes. See
`app-ui-service/README.md` for how the OpenAPI spec and JSON Schemas map to
the Java client/DTO classes in this scaffold, and how to wire in a real code
generator (e.g. `openapi-generator-maven-plugin` / `jsonschema2pojo`) later.
