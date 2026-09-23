"""Slice 04 validation bridge for trusted MCP tool references."""
from __future__ import annotations
from collections.abc import Mapping
from mcp_tools.registry import MCPToolRegistry
from .models import ValidationIssue

def validate_mcp_tool_references(*, workflow_metadata: Mapping, registry: MCPToolRegistry) -> tuple[ValidationIssue, ...]:
    issues = []
    for index, node in enumerate(workflow_metadata.get("nodes", [])):
        if not isinstance(node, Mapping) or node.get("type") != "capability": continue
        tool_id = node.get("tool") or node.get("capability")
        if not isinstance(tool_id, str) or not registry.contains(tool_id):
            issues.append(ValidationIssue("MCP_TOOL_NOT_REGISTERED", f"MCP tool is not registered: {tool_id!r}", document_type="workflow", file_name="workflow-definition.md", path=f"nodes[{index}].capability"))
            continue
        tool = registry.get_tool(tool_id); server = registry.get_server(tool.server_id)
        if not tool.enabled: issues.append(ValidationIssue("MCP_TOOL_DISABLED", f"MCP tool is disabled: {tool_id}", document_type="workflow", file_name="workflow-definition.md"))
        if not server.enabled: issues.append(ValidationIssue("MCP_SERVER_DISABLED", f"MCP server is disabled: {server.server_id}", document_type="workflow", file_name="workflow-definition.md"))
    return tuple(issues)
