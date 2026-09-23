# Slice 09: central LangGraph runtime

This slice makes registered declarative agents executable through one central
LangGraph runtime. It resolves only explicitly registered agents, normalizes and
compiles on first use, caches by application/agent/version/fingerprint, invokes
with a LangGraph thread ID, and exposes state retrieval when the compiled graph
supports it.

It does not use or wrap the legacy WorkflowEngine. Interrupt resume, production
checkpointer creation, Runtime Service migration, and application conversion
remain separate later slices.
