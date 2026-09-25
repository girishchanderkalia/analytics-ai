# Slice 13K Analytics Foundation MCP ASGI fix

Slice 13D supplied a provider library but no ASGI entry point. Slice 13K starts
`analytics_foundation_mcp.app:app`, so this patch adds that HTTP/MCP adapter.

The adapter exposes `/health`, `/ready`, and JSON-RPC `tools/list` and
`tools/call` on `/mcp`.
