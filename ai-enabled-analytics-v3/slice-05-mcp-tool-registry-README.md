# Slice 05: MCP Tool Registry

Adds a trusted in-memory MCP server/tool registry, policy enforcement, input and output schema validation, invocation auditing, safe discovery drift checks, an Execution Engine capability adapter, Slice 04 validation bridge, and read-only control-plane routes.

## Deferred

Dynamic endpoint registration, credential management UI, persistent admin editing, automatic registration of discovered tools, and public direct tool invocation.

## Integration

Mount the router with `app.include_router(mcp_tool_routes.router)` and set `app.state.mcp_tool_registry` plus `app.state.mcp_client`. The capability dispatcher remains compatible with the existing Execution Engine interface.

## Test

```bash
PYTHONPATH=".:./agent-framework/agent-runtime" python -m pytest tests/test_mcp_tool_registry.py tests/test_mcp_tool_invocation.py -v --tb=short
```
