"""Compatibility entry point for the Markdown-declared OPO agent."""

from __future__ import annotations

from typing import Any

from .agent_host import build_agent_graph


def build_graph(definitions=None, dispatcher: Any = None):
    """Build the graph from the Markdown definition bundle at runtime."""
    return build_agent_graph(definitions, dispatcher=dispatcher)
