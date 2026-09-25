# Slice 13H: OPO capability service

Adds a separately deployable MCP service for the three application-owned tools declared in Slice 13G. The service delegates only to Slice 13F pure deterministic logic.

## Install and test

```bash
python -m pip install -e ./app-ui/opo-monitoring/opo-monitoring-service/opo-deterministic-logic
python -m pip install -e ./app-ui/opo-monitoring/opo-monitoring-service/opo-capability-service
python -m pytest app-ui/opo-monitoring/opo-monitoring-service/opo-capability-service/tests -v --tb=short
```

## Full suite

```bash
PYTHONPATH=".;./agent-framework/agent-runtime" python -m pytest tests analytics-foundation/analytics-foundation-api/tests analytics-foundation/analytics-foundation-client/tests analytics-foundation/analytics-foundation-mcp/tests app-ui/opo-monitoring/opo-monitoring-service/opo-deterministic-logic/tests app-ui/opo-monitoring/opo-monitoring-service/opo-capability-service/tests -q --tb=short
```

## Boundary

The service owns OPO calculations only. Analytics Foundation retrieval remains in the Foundation MCP provider. Runtime registration is deferred to Slice 13I.
