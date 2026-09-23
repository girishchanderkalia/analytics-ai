"""Trusted bootstrap helpers for MCP server and tool registrations."""
from __future__ import annotations
from collections.abc import Iterable
from mcp_tools.models import MCPServerRegistration, MCPToolRegistration
from mcp_tools.registry import MCPToolRegistry

def create_mcp_tool_registry(*, servers: Iterable[MCPServerRegistration], tools: Iterable[MCPToolRegistration]) -> MCPToolRegistry:
    registry = MCPToolRegistry()
    for server in servers: registry.register_server(server)
    for tool in tools: registry.register_tool(tool)
    return registry
