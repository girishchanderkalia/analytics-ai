"""Errors raised by governed MCP tool execution."""
class MCPToolError(RuntimeError): pass
class MCPRegistrationError(MCPToolError): pass
class MCPToolNotFoundError(MCPToolError): pass
class MCPServerNotFoundError(MCPToolError): pass
class MCPToolAuthorizationError(MCPToolError): pass
class MCPToolApprovalRequiredError(MCPToolAuthorizationError): pass
class MCPToolSchemaError(MCPToolError): pass
class MCPToolInvocationError(MCPToolError): pass
