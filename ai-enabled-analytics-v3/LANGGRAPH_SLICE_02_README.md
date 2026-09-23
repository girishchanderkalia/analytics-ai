# LangGraph migration, slice 02: atomic bulk agent registration

This additive slice lets trusted prebuilt applications explicitly register one
or more declarative agent packages. The framework does not scan repositories or
automatically discover agents.

## Adds

- immutable registration models
- application-scoped registration keys
- a thread-safe in-memory registration catalog
- an atomic bulk registration service
- a validator protocol for the later Markdown validation slice
- model, catalog, and transaction tests

## Transaction behavior

All submitted agents are validated before any catalog change. If validation or
catalog commit fails, none of the new registrations are stored.

## Not included yet

- HTTP endpoints
- Markdown package loading and validation
- persistent registration storage
- MCP tool validation
- LangGraph compilation
- end-user registration

## Validate

```bash
python -m compileall agent-runtime/agent_registration tests/agent_registration -q
PYTHONPATH=".:./agent-runtime" python -m pytest tests/agent_registration -v --tb=short
PYTHONPATH=".:./agent-runtime" python -m pytest tests -q
```
