from __future__ import annotations
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"agent-runtime"))
from mcp_tools.audit import InMemoryMCPToolAuditSink
from mcp_tools.client import MCPToolResult
from mcp_tools.errors import MCPToolApprovalRequiredError, MCPToolSchemaError
from mcp_tools.invocation import MCPToolInvoker
from mcp_tools.models import MCPApprovalMode, MCPServerRegistration, MCPToolRegistration, MCPToolSecurityContext
from mcp_tools.policy import MCPToolPolicy
from mcp_tools.registry import MCPToolRegistry
class Client:
    def call_tool(self, **kwargs): return MCPToolResult(structured_content={"rows": []})
def setup():
    r=MCPToolRegistry(); r.register_server(MCPServerRegistration("af","AF","streamable-http","https://invalid")); r.register_tool(MCPToolRegistration("query.read","af","read","Read","Read",{"type":"object","properties":{"filters":{"type":"object"}},"required":["filters"]},{"type":"object","properties":{"rows":{"type":"array"}},"required":["rows"]},frozenset({"query:read"}),MCPApprovalMode.ALWAYS)); a=InMemoryMCPToolAuditSink(); return MCPToolInvoker(registry=r,client=Client(),policy=MCPToolPolicy(),audit_sink=a),a
def test_approval_required():
    inv,_=setup()
    with pytest.raises(MCPToolApprovalRequiredError): inv.invoke(tool_id="query.read",arguments={"filters":{}},security_context=MCPToolSecurityContext("agent","conv",frozenset({"query:read"})))
def test_invocation_and_audit():
    inv,a=setup(); result=inv.invoke(tool_id="query.read",arguments={"filters":{}},security_context=MCPToolSecurityContext("agent","conv",frozenset({"query:read"}),frozenset({"query.read"}))); assert result=={"rows":[]}; assert a.events[-1].outcome=="success"
def test_schema_validation_before_call():
    inv,_=setup()
    with pytest.raises(MCPToolSchemaError): inv.invoke(tool_id="query.read",arguments={},security_context=MCPToolSecurityContext("agent","conv",frozenset({"query:read"}),frozenset({"query.read"})))
