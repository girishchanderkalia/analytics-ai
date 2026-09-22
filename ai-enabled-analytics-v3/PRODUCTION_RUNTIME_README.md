# Revised Production Runtime Composition

This revision removes dynamic component-factory environment variables. The
framework continues to own its fixed model gateway, capability dispatcher,
operation registry, and contract provider.

## Only runtime environment variable introduced by this patch

```text
AGENT_RUNTIME_DATABASE_PATH
```

The repository root is derived from the installed source location. The maximum
workflow step limit is fixed in framework code at 100.

## Framework bootstrap

The existing framework bootstrap constructs the fixed `ExecutionContext` and
passes it to the production application builder:

```python
from runtime_api import create_production_app

app = create_production_app(execution_context)
```

No Python implementation classes or factories are selected through environment
variables.

## Validate

```bash
python -m pip install -r agent-runtime/requirements.txt
python -m compileall agent-runtime tests -q
PYTHONPATH="./agent-runtime" python -m pytest tests/test_production_runtime_composition.py -v
PYTHONPATH="./agent-runtime" python -m pytest tests -q
```
