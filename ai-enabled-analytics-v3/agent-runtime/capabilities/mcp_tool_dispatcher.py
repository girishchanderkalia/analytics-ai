"""Execution Engine capability adapter backed by MCP tools."""
from __future__ import annotations
from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from mcp_tools.invocation import MCPToolInvoker
from mcp_tools.models import MCPToolSecurityContext

class MCPToolCapabilityDispatcher:
    def __init__(self, *, invoker: MCPToolInvoker, declarations: Mapping[str, Mapping[str, Any]], agent_id: str) -> None:
        self.invoker, self.declarations, self.agent_id = invoker, {k: dict(v) for k,v in declarations.items()}, agent_id
    def invoke(self, *, capability_id: str, state: Mapping[str, Any], permissions: frozenset[str], approved_capabilities: frozenset[str]) -> Mapping[str, Any]:
        declaration = self.declarations[capability_id]
        mapping = declaration.get("input") or declaration.get("input_from") or {}
        arguments = {str(target): deepcopy(state[source]) for target, source in mapping.items()}
        output = self.invoker.invoke(tool_id=str(declaration.get("tool", capability_id)), arguments=arguments, security_context=MCPToolSecurityContext(agent_id=self.agent_id, conversation_id=str(state.get("conversation_id", "unknown")), user_id=state.get("user_id"), permissions=permissions, approved_tools=approved_capabilities, allowed_tools=frozenset(str(v.get("tool", k)) for k,v in self.declarations.items())))
        return {str(declaration["output_to"]): dict(output)}
