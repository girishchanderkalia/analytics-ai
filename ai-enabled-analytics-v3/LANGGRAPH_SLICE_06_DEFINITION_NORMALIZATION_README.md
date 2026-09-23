# Slice 06: generic definition normalization

This slice converts generic package sources into domain-neutral normalized
models that later slices will compile into LangGraph.

The normalizer validates topology and generic source shape only. It does not
interpret application vocabulary, domain state fields, prompt semantics, MCP
tool implementation, or organization-specific policy.

Node `kind` remains an opaque string in this slice. The standard node-library
slice will resolve supported kinds without adding application-specific kinds.
