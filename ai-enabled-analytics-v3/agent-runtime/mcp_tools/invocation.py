"""Governed MCP tool invocation service."""
from __future__ import annotations
from collections.abc import Mapping
from time import monotonic
from typing import Any
from uuid import uuid4
from .audit import MCPToolAuditEvent, MCPToolAuditSink
from .client import MCPClient
from .errors import MCPToolInvocationError
from .models import MCPToolSecurityContext
from .policy import MCPToolPolicy
from .registry import MCPToolRegistry
from .schema_validation import validate_instance

class MCPToolInvoker:
    def __init__(self, *, registry: MCPToolRegistry, client: MCPClient, policy: MCPToolPolicy, audit_sink: MCPToolAuditSink) -> None:
        self.registry, self.client, self.policy, self.audit_sink = registry, client, policy, audit_sink
    def invoke(self, *, tool_id: str, arguments: Mapping[str, Any], security_context: MCPToolSecurityContext) -> Mapping[str, Any]:
        invocation_id, started = str(uuid4()), monotonic()
        tool = self.registry.get_tool(tool_id); server = self.registry.get_server(tool.server_id)
        approved = tool_id in security_context.approved_tools
        try:
            self.policy.authorize(tool=tool, server=server, security_context=security_context)
            validate_instance(arguments, tool.input_schema, "tool arguments")
            result = self.client.call_tool(server=server, tool_name=tool.remote_name, arguments=arguments, timeout_seconds=tool.timeout_seconds or server.timeout_seconds)
            if result.is_error: raise MCPToolInvocationError("MCP tool returned an error")
            output = result.structured_content
            if output is None: raise MCPToolInvocationError("MCP tool returned no structured content")
            if tool.output_schema is not None: validate_instance(output, tool.output_schema, "tool output")
            self._audit(invocation_id, security_context, tool_id, server.server_id, approved, "success", started, None)
            return dict(output)
        except Exception as exc:
            self._audit(invocation_id, security_context, tool_id, server.server_id, approved, "failed", started, type(exc).__name__)
            raise
    def _audit(self, invocation_id, context, tool_id, server_id, approved, outcome, started, error_code):
        self.audit_sink.record(MCPToolAuditEvent(invocation_id, context.conversation_id, context.agent_id, context.user_id, tool_id, server_id, approved, outcome, int((monotonic()-started)*1000), error_code))
