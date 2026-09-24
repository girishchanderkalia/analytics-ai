# Slice 13H: OPO capability service

Adds a separately deployable MCP service for the three application-owned tools declared in Slice 13G. The service delegates only to Slice 13F pure deterministic logic.

## Install and test

```bash
python -m pip install -e ./opo-deterministic-logic
python -m pip install -e ./opo-capability-service
python -m pytest opo-capability-service/tests -v --tb=short
```

## Full suite

```bash
PYTHONPATH=".;./agent-runtime" python -m pytest tests analytics-foundation-api/tests analytics-foundation-client/tests analytics-foundation-mcp/tests opo-deterministic-logic/tests opo-capability-service/tests -q --tb=short
```

## Boundary

The service owns OPO calculations only. Analytics Foundation retrieval remains in the Foundation MCP provider. Runtime registration is deferred to Slice 13I.
