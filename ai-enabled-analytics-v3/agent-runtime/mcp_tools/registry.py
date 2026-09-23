"""Trusted in-memory MCP server and tool registry."""
from __future__ import annotations
from .errors import MCPRegistrationError, MCPServerNotFoundError, MCPToolNotFoundError
from .models import MCPApprovalMode, MCPServerRegistration, MCPToolRegistration
from .schema_validation import validate_schema_definition

class MCPToolRegistry:
    def __init__(self) -> None:
        self._servers: dict[str, MCPServerRegistration] = {}
        self._tools: dict[str, MCPToolRegistration] = {}
    def register_server(self, item: MCPServerRegistration) -> None:
        if not item.server_id.strip() or item.server_id in self._servers: raise MCPRegistrationError("Server ID must be non-empty and unique")
        if item.transport not in {"streamable-http", "sse", "stdio"}: raise MCPRegistrationError("Unsupported MCP transport")
        if not item.endpoint.strip() or item.timeout_seconds <= 0: raise MCPRegistrationError("Server endpoint and timeout are invalid")
        self._servers[item.server_id] = item
    def register_tool(self, item: MCPToolRegistration) -> None:
        if not item.tool_id.strip() or item.tool_id in self._tools: raise MCPRegistrationError("Tool ID must be non-empty and unique")
        if item.server_id not in self._servers: raise MCPServerNotFoundError(item.server_id)
        if not item.remote_name.strip(): raise MCPRegistrationError("Remote tool name must be non-empty")
        validate_schema_definition(item.input_schema, "input_schema")
        if item.output_schema is not None: validate_schema_definition(item.output_schema, "output_schema")
        if item.timeout_seconds is not None and item.timeout_seconds <= 0: raise MCPRegistrationError("Tool timeout must be positive")
        self._tools[item.tool_id] = item
    def unregister_tool(self, tool_id: str) -> None:
        if tool_id not in self._tools: raise MCPToolNotFoundError(tool_id)
        del self._tools[tool_id]
    def get_tool(self, tool_id: str) -> MCPToolRegistration:
        try: return self._tools[tool_id]
        except KeyError as exc: raise MCPToolNotFoundError(tool_id) from exc
    def get_server(self, server_id: str) -> MCPServerRegistration:
        try: return self._servers[server_id]
        except KeyError as exc: raise MCPServerNotFoundError(server_id) from exc
    def contains(self, tool_id: str) -> bool: return tool_id in self._tools
    def list_tools(self, *, enabled_only: bool = True, tags: frozenset[str] | None = None) -> tuple[MCPToolRegistration, ...]:
        values = self._tools.values()
        if enabled_only: values = (item for item in values if item.enabled)
        if tags: values = (item for item in values if tags <= item.tags)
        return tuple(sorted(values, key=lambda item: item.tool_id))
    def list_servers(self, *, enabled_only: bool = True) -> tuple[MCPServerRegistration, ...]:
        values = self._servers.values()
        if enabled_only: values = (item for item in values if item.enabled)
        return tuple(sorted(values, key=lambda item: item.server_id))
