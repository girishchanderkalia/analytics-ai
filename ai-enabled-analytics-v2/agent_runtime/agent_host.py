"""Generic agent host for fully declarative agent definitions."""

from __future__ import annotations

from typing import Any

from .declarative_runtime import DeclarativeAgent


def build_agent_graph(definitions=None, dispatcher: Any = None):
    return DeclarativeAgent(definitions, dispatcher=dispatcher).build_graph()
