from fastapi import Request
from mcp_tools.registry import MCPToolRegistry
from mcp_tools.client import MCPClient

def get_mcp_registry(request: Request) -> MCPToolRegistry:
    value = getattr(request.app.state, "mcp_tool_registry", None)
    if value is None: raise RuntimeError("MCP Tool Registry is not configured")
    return value

def get_mcp_client(request: Request) -> MCPClient:
    value = getattr(request.app.state, "mcp_client", None)
    if value is None: raise RuntimeError("MCP client is not configured")
    return value
