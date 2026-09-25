# Slice 11: LangGraph Checkpointer

This slice adds framework-owned checkpointer composition for memory, SQLite,
and PostgreSQL backends. Optional SQLite and PostgreSQL dependencies are loaded
lazily. The public runtime continues to expose only `conversationId`; LangGraph
`thread_id`, checkpoint namespace, and checkpoint IDs remain internal.

## Environment

```text
AGENT_RUNTIME_CHECKPOINTER_BACKEND=memory|sqlite|postgres
AGENT_RUNTIME_CHECKPOINTER_CONNECTION_STRING=
AGENT_RUNTIME_CHECKPOINTER_SETUP=false
```

Use `memory` only for tests and local ephemeral execution. Use a shared durable
backend before scaling the Agent Runtime to multiple replicas.

## Compile and test in Git Bash with Windows Python

```bash
python -m compileall agent-runtime/langgraph_runtime/checkpointing tests/langgraph_runtime -q
PYTHONPATH=".;./agent-framework/agent-runtime" python -m pytest tests/langgraph_runtime/test_checkpointer.py -v --tb=short
PYTHONPATH=".;./agent-framework/agent-runtime" python -m pytest tests -q --tb=short
```

## Integration

Pass `handle.checkpointer` into the Slice 08 compiler's `checkpointer` argument.
Keep the `CheckpointerHandle` alive for the application lifetime and call
`handle.close()` during application shutdown.
