# Registered Production Application Bootstrap

This slice introduces one validated application-registration object containing:

- the governed Capability Registry
- application-owned deterministic operations
- the execution security policy

`create_registered_production_app()` consumes those registrations and creates
the persisted FastAPI application. Contract Providers remain per-agent and are
created only after agent resolution.

This patch intentionally does not invent concrete production capability-client
constructors or an `analyse_trends` import path. Those implementations already
belong to the application and platform adapter modules in the repository and
must be supplied by the concrete application bootstrap.

## Validate

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH=".:./agent-framework/agent-runtime" python -m pytest tests/test_registered_production_app.py -v
PYTHONPATH=".:./agent-framework/agent-runtime" python -m pytest tests -q
```
