# Final per-agent Runtime Composer

This patch completes per-agent engine composition. Platform-wide model and
capability dependencies are reused, application operations are registered once,
and contracts are resolved only after an agent bundle is selected.

It also corrects `RuntimeContextFactory` so `ExecutionSecurityContext` is the
single source for permissions and approved capabilities.

Validate with:

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH=".:./agent-runtime" python -m pytest tests/test_fixed_runtime_composer.py -v
PYTHONPATH=".:./agent-runtime" python -m pytest tests -q
```
