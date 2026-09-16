"""MCP Capability Adaptor: the only path from the agent runtime to Foundation APIs.

Exposes typed, validated, policy-governed tools (never a raw passthrough) per
``agentWorkflows/mcp-oss-target-architecture.puml``. Each server module wraps the
implementation in ``foundation/clients/*.py``. See PLAN.md Phase 3.
"""
