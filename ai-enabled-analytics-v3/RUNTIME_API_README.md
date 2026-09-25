# Application Agent Runtime API patch

This additive patch introduces the FastAPI transport layer over the existing
Agent Catalog and Agent Host.

## Included

- FastAPI application factory and ASGI entry point
- Start, resume, catalog, and health endpoints
- Pydantic request and response models
- Dependency injection through `app.state.agent_host`
- Stable runtime-to-HTTP error mapping
- FastAPI contract tests using `TestClient`
- Dependency updates in `agent-framework/agent-runtime/requirements.txt`

## Extract

Extract this ZIP at the `ai-enabled-analytics-v3` repository root.

## Install

```bash
python -m pip install -r agent-framework/agent-runtime/requirements.txt
```

## Validate

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH="./agent-framework/agent-runtime" python -m pytest tests/test_runtime_api.py -v
PYTHONPATH="./agent-framework/agent-runtime" python -m pytest tests -q
```

## Production composition

Create the FastAPI application with the composed Agent Host:

```python
from runtime_api import create_app

app = create_app(agent_host)
```

The default `runtime_api.main:app` deliberately has no configured host. The
health endpoint remains available, while host-dependent endpoints return a
structured HTTP 503 response until dependency composition is provided.
