# Slice 13D: MCP-to-Foundation migration

Adds a standalone MCP tool provider backed by the shared Analytics Foundation
HTTP client. The package is additive and preserves the existing
`McpToolRegistry` implementation.

## Install

```bash
python -m pip install -e ./analytics-foundation/analytics-foundation-client
python -m pip install -e ./analytics-foundation/analytics-foundation-mcp
```

## Focused tests

```bash
PYTHONPATH="./agent-framework/agent-runtime;./analytics-foundation/analytics-foundation/analytics-foundation/analytics-foundation-client/src;./analytics-foundation/analytics-foundation/analytics-foundation/analytics-foundation-mcp/src" \
python -m pytest analytics-foundation/analytics-foundation-mcp/tests -v --tb=short
```
