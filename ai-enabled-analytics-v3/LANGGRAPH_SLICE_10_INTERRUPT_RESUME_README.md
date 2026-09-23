# Slice 10: LangGraph interrupt and resume

This slice surfaces LangGraph interrupt IDs and payloads as generic runtime
results and resumes the same thread using `Command(resume=...)`. A checkpointer
is required for resume. Targeted resume uses `{interrupt_id: value}`; untargeted
resume passes a single value to the next interrupt.

The implementation contains no application-specific approval vocabulary or
business logic. Persistent checkpointer construction remains Slice 11.
