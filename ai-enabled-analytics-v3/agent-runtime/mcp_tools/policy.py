"""Authorization and approval policy for MCP tools."""
from .errors import MCPToolApprovalRequiredError, MCPToolAuthorizationError
from .models import MCPApprovalMode, MCPServerRegistration, MCPToolRegistration, MCPToolSecurityContext

class MCPToolPolicy:
    def authorize(self, *, tool: MCPToolRegistration, server: MCPServerRegistration, security_context: MCPToolSecurityContext) -> None:
        if not server.enabled: raise MCPToolAuthorizationError("MCP server is disabled")
        if not tool.enabled: raise MCPToolAuthorizationError("MCP tool is disabled")
        if security_context.allowed_tools and tool.tool_id not in security_context.allowed_tools: raise MCPToolAuthorizationError("Agent is not allowed to use this MCP tool")
        missing = tool.required_permissions - security_context.permissions
        if missing: raise MCPToolAuthorizationError("Missing permissions: " + ", ".join(sorted(missing)))
        approval = tool.approval_mode == MCPApprovalMode.ALWAYS or (tool.approval_mode == MCPApprovalMode.WRITE and tool.mutating)
        if approval and tool.tool_id not in security_context.approved_tools: raise MCPToolApprovalRequiredError(f"MCP tool {tool.tool_id!r} requires approval")
