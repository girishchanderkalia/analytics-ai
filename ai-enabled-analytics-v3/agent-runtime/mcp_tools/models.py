"""MCP registry domain models."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

class MCPApprovalMode(StrEnum):
    NEVER = "never"
    ALWAYS = "always"
    WRITE = "write"

@dataclass(frozen=True)
class MCPServerRegistration:
    server_id: str
    display_name: str
    transport: str
    endpoint: str
    enabled: bool = True
    authentication_profile: str | None = None
    timeout_seconds: float = 30.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class MCPToolRegistration:
    tool_id: str
    server_id: str
    remote_name: str
    title: str
    description: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any] | None = None
    required_permissions: frozenset[str] = frozenset()
    approval_mode: MCPApprovalMode = MCPApprovalMode.NEVER
    enabled: bool = True
    mutating: bool = False
    timeout_seconds: float | None = None
    tags: frozenset[str] = frozenset()

@dataclass(frozen=True)
class MCPToolSecurityContext:
    agent_id: str
    conversation_id: str
    permissions: frozenset[str] = frozenset()
    approved_tools: frozenset[str] = frozenset()
    allowed_tools: frozenset[str] = frozenset()
    user_id: str | None = None
