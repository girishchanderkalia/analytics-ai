from __future__ import annotations
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"agent-runtime"))
from mcp_tools.errors import MCPRegistrationError, MCPServerNotFoundError
from mcp_tools.models import MCPApprovalMode, MCPServerRegistration, MCPToolRegistration
from mcp_tools.registry import MCPToolRegistry

def server(): return MCPServerRegistration("af", "Analytics Foundation", "streamable-http", "https://example.invalid/mcp")
def tool(**changes):
    values=dict(tool_id="query.read", server_id="af", remote_name="read", title="Read", description="Read data", input_schema={"type":"object","properties":{},"required":[]}, tags=frozenset({"query"})); values.update(changes); return MCPToolRegistration(**values)
def test_register_and_list():
    r=MCPToolRegistry(); r.register_server(server()); r.register_tool(tool()); assert r.contains("query.read"); assert r.list_tools()[0].tool_id=="query.read"
def test_duplicate_server_rejected():
    r=MCPToolRegistry(); r.register_server(server())
    with pytest.raises(MCPRegistrationError): r.register_server(server())
def test_unknown_server_rejected():
    r=MCPToolRegistry()
    with pytest.raises(MCPServerNotFoundError): r.register_tool(tool())
def test_tag_filter():
    r=MCPToolRegistry(); r.register_server(server()); r.register_tool(tool()); assert len(r.list_tools(tags=frozenset({"query"})))==1
