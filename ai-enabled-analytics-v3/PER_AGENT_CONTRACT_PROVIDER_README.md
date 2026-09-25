# Per-agent Contract Provider

This patch creates typed Pydantic contracts from each resolved agent bundle.
Providers are isolated and cached by agent ID and version.

The agent definition remains the source for contract names, fields, types,
defaults, descriptions, and literal values. A workflow can only request a
contract declared by its own agent version.

The existing contract definition format in `agent-definition.md` is preserved.
No Python contract implementation or import path is configured through an
environment variable.

## Validate

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH=".:./agent-framework/agent-runtime" python -m pytest tests/test_per_agent_contract_provider.py -v
PYTHONPATH=".:./agent-framework/agent-runtime" python -m pytest tests -q
```
