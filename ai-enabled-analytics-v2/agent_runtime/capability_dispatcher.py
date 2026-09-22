"""Generic capability dispatch boundary for Markdown-defined agents."""

from __future__ import annotations

from typing import Any, Callable


class CapabilityDispatcher:
    """Dispatch declared capability IDs to platform adaptors.

    Agent definitions select capability IDs; platform composition supplies the
    implementation map. No agent-specific handler is required.
    """

    def __init__(self, operations: dict[str, Callable[[dict[str, Any]], dict[str, Any]]]):
        self.operations = operations

    def invoke(self, capability_id: str, state: dict[str, Any]) -> dict[str, Any]:
        try:
            operation = self.operations[capability_id]
        except KeyError as exc:
            raise KeyError(f"No platform adaptor registered for {capability_id}") from exc
        return operation(state)
