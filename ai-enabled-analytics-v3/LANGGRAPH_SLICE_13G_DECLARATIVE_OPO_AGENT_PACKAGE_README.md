# Slice 13G: Declarative OPO agent package

Adds the application-owned OPO package under `app-ui/opo-monitoring/agent`.
The package declares workflow, state, prompts, MCP tool references and knowledge.
It contains no runtime construction, HTTP client, checkpoint or database code.

The `opo-capability` tool references are intentionally marked for Slice 13H.

## Focused test

```bash
python -m pytest app-ui/opo-monitoring/agent/tests -v --tb=short
```
