# Slice 13A: Analytics Foundation API contract

This slice introduces an additive OpenAPI 3.0.3 contract for a separately
deployable Analytics Foundation API.

Consumers:
- Java application BFF for deterministic application flows.
- MCP analytics tools for agent-controlled flows.

The contract intentionally excludes chat, resume, prompts, findings, human
approval, and graph execution.
