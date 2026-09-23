# LangGraph migration, slice 01: core runtime foundation

This additive slice establishes the new LangGraph-centered package without
changing the existing execution path.

## LanGraph package

Dependency: LangGraph
Version: 1.2.11
Package: https://pypi.org/project/langgraph/
Source: https://github.com/langchain-ai/langgraph
License: MIT
Usage: Stateful graph orchestration runtime
Vendored source: No
Installation: PyPI through requirements-langgraph.txt

## Adds

- generic graph state
- graph dependency container
- centralized LangGraph runtime errors
- a lazy LangGraph installation check
- an additive LangGraph requirements file
- domain-neutral unit tests

## Does not yet add

- MCP tool discovery
- Markdown normalization
- nodes
- graph compilation
- checkpoints
- interrupts
- Runtime Service integration

## Install

```bash
python -m pip install -r agent-runtime/requirements-langgraph.txt
```

## Validate

```bash
python -m compileall agent-runtime/langgraph_runtime tests/langgraph_runtime -q
PYTHONPATH=".:./agent-runtime" python -m pytest tests/langgraph_runtime -v --tb=short
PYTHONPATH=".:./agent-runtime" python -m pytest tests -q
```

