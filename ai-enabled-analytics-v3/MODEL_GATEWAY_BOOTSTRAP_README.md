# Fixed Model Gateway Bootstrap

This patch wires the existing fixed platform Model Gateway into the declarative
Workflow Engine without selecting implementation classes through environment
variables.

The existing `foundation.model_gateway.get_model()` remains the source of the
configured hosted model. `PlatformModelGateway` adapts that model to the
`invoke_structured()` interface used by model workflow nodes.

## Architecture

```text
foundation.model_gateway.get_model()
        ↓
PlatformModelGateway
        ↓
ExecutionContext.model_gateway
        ↓
Workflow Engine model node
```

The fixed Model Gateway obtains endpoint, API version, deployment, and API key
through its existing `foundation.config` path. This patch does not introduce
new Model Gateway environment variables.

## Apply

Extract this archive at the repository root.

## Validate

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH="./agent-runtime" python -m pytest tests/test_model_gateway_bootstrap.py -v
PYTHONPATH="./agent-runtime" python -m pytest tests -q
```
