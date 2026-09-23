"""Safe discovery and drift verification for registered MCP servers."""
from __future__ import annotations
from dataclasses import dataclass
from .client import MCPClient
from .registry import MCPToolRegistry

@dataclass(frozen=True)
class MCPToolVerificationResult:
    server_id: str
    available: tuple[str, ...]
    missing: tuple[str, ...]
    schema_mismatches: tuple[str, ...]
    unregistered_remote_tools: tuple[str, ...]

def verify_server(*, registry: MCPToolRegistry, client: MCPClient, server_id: str) -> MCPToolVerificationResult:
    server = registry.get_server(server_id)
    discovered = {item.name: item for item in client.list_tools(server=server)}
    registered = {item.remote_name: item for item in registry.list_tools(enabled_only=False) if item.server_id == server_id}
    available = tuple(sorted(set(registered) & set(discovered)))
    missing = tuple(sorted(set(registered) - set(discovered)))
    mismatches = tuple(sorted(name for name in available if dict(registered[name].input_schema) != dict(discovered[name].input_schema)))
    unknown = tuple(sorted(set(discovered) - set(registered)))
    return MCPToolVerificationResult(server_id, available, missing, mismatches, unknown)
