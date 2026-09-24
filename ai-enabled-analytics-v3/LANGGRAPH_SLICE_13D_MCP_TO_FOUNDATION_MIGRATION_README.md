# Slice 13D: MCP-to-Foundation migration

Adds a standalone MCP tool provider backed by the shared Analytics Foundation
HTTP client. The package is additive and preserves the existing
`McpToolRegistry` implementation.

## Install

```bash
python -m pip install -e ./analytics-foundation-client
python -m pip install -e ./analytics-foundation-mcp
```

## Focused tests

```bash
PYTHONPATH="./agent-runtime;./analytics-foundation-client/src;./analytics-foundation-mcp/src" \
python -m pytest analytics-foundation-mcp/tests -v --tb=short
```
