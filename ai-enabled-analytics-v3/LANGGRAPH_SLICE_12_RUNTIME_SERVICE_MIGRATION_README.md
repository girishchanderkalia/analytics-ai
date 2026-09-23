# Slice 12: Runtime Service migration

This additive slice introduces a transport-neutral Runtime Service facade that
routes start, resume, and state retrieval exclusively through
`LangGraphAgentRuntime`. The conversation ID becomes LangGraph's thread ID.

The slice also provides a lifecycle composition boundary that starts the
persistent checkpointer before constructing the central runtime and shuts down
the checkpointer during application shutdown.

The legacy Runtime Service is not overwritten in this ZIP because its current
public request and response types were not part of the supplied Slice 12 input.
Applications can adopt this facade directly, or a thin API adapter can map the
existing HTTP contract to these models without reintroducing WorkflowEngine.
