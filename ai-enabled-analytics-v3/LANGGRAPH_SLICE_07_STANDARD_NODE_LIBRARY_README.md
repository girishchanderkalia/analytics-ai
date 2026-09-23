# Slice 07: standard LangGraph node library

This slice adds four reusable framework node kinds:

- `model`
- `tool`
- `transform`
- `interrupt`

No application-specific node class is introduced. Application behavior remains
in normalized configuration, prompts, state, knowledge, and MCP tools.

The interrupt node imports LangGraph lazily and supports an injected interrupt
function for isolated tests. The compiler slice will place these node callables
inside a real `StateGraph`.
