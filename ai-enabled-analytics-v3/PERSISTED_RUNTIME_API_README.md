# Persisted Runtime API integration

This patch replaces client-supplied workflow state on resume with durable
conversation lookup through the Runtime Service.

## Endpoints

- `GET /health`
- `POST /v1/chat`
- `POST /v1/conversations/{conversation_id}/resume`
- `GET /v1/conversations/{conversation_id}`

## Apply

Extract at the `ai-enabled-analytics-v3` repository root after applying the
persistence and Runtime Service ZIPs.

## Validate

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH="./agent-runtime" python -m pytest tests/test_persisted_runtime_api.py -v
PYTHONPATH="./agent-runtime" python -m pytest tests -q
```

The prior `tests/test_runtime_api.py` tests the stateless Agent Host API. This
patch changes the public runtime API to the persisted Runtime Service contract.
Remove or archive `tests/test_runtime_api.py` if both API contracts should not
coexist in the same repository.
