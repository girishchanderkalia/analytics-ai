# Fixed Operation Registry Bootstrap

This patch wires application-owned deterministic operations into the existing
framework `OperationRegistry`.

The Framework creates the registry. Application bootstrap code supplies an
explicit mapping from declarative operation names to Python callables, for
example:

```python
operations = {
    "analyse_trends": analyse_trends,
}
```

No operation implementation is selected through environment variables.
Workflow validation can check that every node of type `operation` has a
registered handler before execution begins.

## Validate

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH=".:./agent-runtime" python -m pytest tests/test_operation_registry_bootstrap.py -v
PYTHONPATH=".:./agent-runtime" python -m pytest tests -q
```
