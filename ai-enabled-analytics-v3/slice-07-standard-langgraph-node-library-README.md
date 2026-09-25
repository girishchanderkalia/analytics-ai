# Slice 07: Standard LangGraph Node Library

This additive slice provides reusable framework-owned node factories for structured model calls, governed tools, contract validation, approval interrupts, deterministic state updates, and conditional routing.

## Dependency contracts

The existing `GraphDependencies` fields are used without replacing current runtime implementations:

- `model_provider.invoke_structured(...)`
- `tool_registry.invoke(...)`
- `contract_provider.get_contract(...)`
- `prompt_provider.get_prompt(...)`
- `expression_engine.evaluate(...)`
- `security_context`

## State contract

Every node validates the incoming graph state through the existing `copy_graph_state()` boundary and returns a partial state update suitable for LangGraph.

## Test

```bash
PYTHONPATH=".;./agent-framework/agent-runtime" python -m pytest tests/langgraph_runtime/test_standard_nodes.py -v --tb=short
```

This command uses `;` because Git Bash is launching Windows Python in the current development environment.
