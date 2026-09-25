# Slice 13K: End-to-end integration

This slice adds black-box integration tests across the Analytics Foundation API,
Foundation MCP provider, OPO capability MCP service, shared Agent Runtime, and
Java application BFF.

## Test without model-backed chat

```bash
python -m pip install -e ./integration-tests
python -m pytest integration-tests/tests -m "smoke or deterministic" -v --tb=short
```

## Full model-backed flow

```bash
export RUN_AGENT_E2E=true
python -m pytest integration-tests/tests -v --tb=short
```

The environment URLs are documented in `integration-tests/.env.example`.
The Compose file is an integration overlay and expects the Agent Runtime and
Foundation MCP images to have been built by their owning slices.
