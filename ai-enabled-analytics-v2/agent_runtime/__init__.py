"""Agent Runtime Framework: LangGraph StateGraph + PydanticAI application agent.

Owns intent -> DetectionScope and evidence -> FindingsSummary only, per
``agentWorkflows/mcp-oss-target-architecture.puml``. No direct API, database,
credential, checkpoint, or audit access — all platform access goes through
``mcp_capability_adaptor``.
"""
