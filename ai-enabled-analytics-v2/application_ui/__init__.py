"""Application UI / BFF: HTTP endpoints, display routes, agent invocation.

Owns application-facing routes only. All Foundation platform access happens
through ``mcp_capability_adaptor.client``; all orchestration happens through
``agent_runtime.graph``. Matches
``agentWorkflows/mcp-oss-target-architecture.puml``'s "Application UI" package.
"""
