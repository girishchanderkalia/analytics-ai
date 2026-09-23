"""Audit contracts for MCP tool invocation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class MCPToolAuditEvent:
    invocation_id: str
    conversation_id: str
    agent_id: str
    user_id: str | None
    tool_id: str
    server_id: str
    approved: bool
    outcome: str
    duration_ms: int
    error_code: str | None = None

class MCPToolAuditSink(Protocol):
    def record(self, event: MCPToolAuditEvent) -> None: ...

class InMemoryMCPToolAuditSink:
    def __init__(self) -> None: self.events: list[MCPToolAuditEvent] = []
    def record(self, event: MCPToolAuditEvent) -> None: self.events.append(event)
