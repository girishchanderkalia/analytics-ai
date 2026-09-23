# Slice 12: Runtime Service migration to central LangGraph runtime

This slice adds an additive LangGraph-backed Runtime Service. It resolves an
active or exact immutable agent version, caches compiled graphs by agent ID,
version and definition digest, starts and resumes through the compiled graph,
and maps interrupts to the existing public approval contract.

The metadata store persists only public conversation metadata. Authoritative
graph state remains in the LangGraph checkpointer.

## Test

```bash
PYTHONPATH=".;./agent-runtime" python -m pytest tests/host/test_langgraph_runtime_service.py tests/host/test_compiled_agent_cache.py tests/host/test_langgraph_result_mapper.py -v --tb=short
PYTHONPATH=".;./agent-runtime" python -m pytest tests -q --tb=short
```

## Integration boundary

Do not remove the previous Runtime Service until API parity tests pass. Wire the
new service behind the existing `/v1/chat` and resume routes through dependency
injection, then delete the old dual execution path in a separate cleanup commit.
