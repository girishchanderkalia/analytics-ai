# Corrected Slice 03: generic agent package

A prebuilt application registers a package containing `agent-package.yaml`.
Only generic source roles are part of framework structure: graph, state,
prompts, tools, knowledge, and optional documentation. Application and
organization-specific content remains inside referenced files.

Only graph and state are required in this slice. It does not validate domain
vocabulary, node kinds, prompts, tools, contracts, or MCP availability.
