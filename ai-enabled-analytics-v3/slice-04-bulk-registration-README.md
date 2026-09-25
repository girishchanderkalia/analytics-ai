# Slice 04: Bulk Agent Registration API

## Scope

This slice adds a framework-owned control-plane API for importing declarative
agent bundles as ZIP files. It supports two safe modes:

- `validate`: validate without persistence
- `create-draft`: validate and persist an editable draft

Publishing and activation are deliberately deferred to the next slice.

## ZIP structure

```text
agent-bundle.zip
├── manifest.json                    required
├── agent-definition.md              required
├── workflow-definition.md           required
├── state-model.md                   required
├── tools-and-capabilities.md         conditional
├── knowledge-model.md                optional
└── sequence-diagrams.md              optional
```

`tools-and-capabilities.md` becomes required when the workflow contains a
capability node.

## Endpoints

```text
GET  /v1/agent-definition-types
POST /v1/agent-bundles/import?mode=validate
POST /v1/agent-bundles/import?mode=create-draft
GET  /v1/agents/{agentId}/drafts/{draftId}
```

The import request body is raw ZIP bytes with `Content-Type: application/zip`.
No multipart dependency is required.

## Security limits

- Flat ZIP only
- No absolute paths or `..`
- Allow-listed canonical file names
- UTF-8 documents only
- 2 MiB archive limit
- 512 KiB per-document limit
- No executable code or endpoint definitions
- Capabilities and operations are references to trusted runtime registrations

## Wiring

Production composition must create `AgentRegistrationService` and pass it to:

```python
create_app(
    runtime_service=runtime_service,
    agent_registration_service=agent_registration_service,
)
```

For local development, use a separate SQLite catalog path from the conversation
store, for example `./var/agent-catalog.sqlite`.

## Test

```bash
PYTHONPATH=".:./agent-framework/agent-runtime" python -m pytest tests/test_bulk_agent_registration.py -v --tb=short
```

Then run the complete suite.
