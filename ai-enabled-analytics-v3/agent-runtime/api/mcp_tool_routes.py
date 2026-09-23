"""Read-only control-plane routes for MCP registry metadata."""
from fastapi import APIRouter, Depends
from mcp_tools.discovery import verify_server
from mcp_tools.registry import MCPToolRegistry
from mcp_tools.client import MCPClient
from .mcp_tool_dependencies import get_mcp_client, get_mcp_registry
router = APIRouter(prefix="/v1/mcp", tags=["mcp-tools"])

@router.get("/tools")
def list_tools(registry: MCPToolRegistry = Depends(get_mcp_registry)):
    return {"tools": [{"toolId": t.tool_id, "serverId": t.server_id, "title": t.title, "description": t.description, "enabled": t.enabled, "approvalMode": t.approval_mode.value, "tags": sorted(t.tags)} for t in registry.list_tools(enabled_only=False)]}

@router.get("/tools/{tool_id}")
def get_tool(tool_id: str, registry: MCPToolRegistry = Depends(get_mcp_registry)):
    t=registry.get_tool(tool_id); return {"toolId": t.tool_id, "serverId": t.server_id, "remoteName": t.remote_name, "title": t.title, "description": t.description, "enabled": t.enabled, "approvalMode": t.approval_mode.value, "requiredPermissions": sorted(t.required_permissions), "inputSchema": dict(t.input_schema), "outputSchema": dict(t.output_schema) if t.output_schema else None, "tags": sorted(t.tags)}

@router.get("/servers")
def list_servers(registry: MCPToolRegistry = Depends(get_mcp_registry)):
    return {"servers": [{"serverId": s.server_id, "displayName": s.display_name, "transport": s.transport, "enabled": s.enabled} for s in registry.list_servers(enabled_only=False)]}

@router.post("/servers/{server_id}/verify")
def verify(server_id: str, registry: MCPToolRegistry = Depends(get_mcp_registry), client: MCPClient = Depends(get_mcp_client)):
    result=verify_server(registry=registry, client=client, server_id=server_id); return {"serverId": result.server_id, "available": result.available, "missing": result.missing, "schemaMismatches": result.schema_mismatches, "unregisteredRemoteTools": result.unregistered_remote_tools}

@router.post("/tools/validate-references")
def validate_references(tool_ids: list[str], registry: MCPToolRegistry = Depends(get_mcp_registry)):
    resolved=[{"toolId": x, "serverId": registry.get_tool(x).server_id, "enabled": registry.get_tool(x).enabled} for x in tool_ids if registry.contains(x)]; missing=sorted(set(tool_ids)-{x["toolId"] for x in resolved}); return {"valid": not missing, "resolved": resolved, "missing": missing}
