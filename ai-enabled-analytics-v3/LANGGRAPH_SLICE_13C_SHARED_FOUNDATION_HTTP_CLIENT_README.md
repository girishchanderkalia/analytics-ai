# Slice 13C: Shared Analytics Foundation HTTP client

Adds a reusable Python async HTTP client aligned with the Slice 13A contract.
The next Slice 13D will inject this client into MCP tools, replacing in-process
mock Foundation imports.

## Focused tests

```bash
PYTHONPATH="./analytics-foundation/analytics-foundation/analytics-foundation/analytics-foundation-client/src" \
python -m pytest analytics-foundation/analytics-foundation-client/tests -v --tb=short
```

## Installation

```bash
python -m pip install -e ./analytics-foundation/analytics-foundation-client
```
