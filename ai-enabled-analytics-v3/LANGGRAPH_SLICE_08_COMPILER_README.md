# Slice 08: LangGraph compiler

This slice compiles normalized definitions into a real LangGraph `StateGraph`.
It registers nodes from the standard node library, creates fixed and conditional
edges, maps declarative `END` targets to LangGraph `END`, builds a dynamic state
schema from the package's JSON Schema, and forwards optional checkpointer/store
objects to `StateGraph.compile()`.

Conditional routes are evaluated in declaration order and require exactly one
default edge. The expression engine remains a generic framework dependency.
