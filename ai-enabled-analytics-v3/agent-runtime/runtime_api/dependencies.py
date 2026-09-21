"""FastAPI dependency providers for runtime services."""

from __future__ import annotations

from typing import Any

from fastapi import Request


class AgentHostUnavailableError(RuntimeError):
    """Raised when the FastAPI application has no configured Agent Host."""


def get_agent_host(request: Request) -> Any:
    """Resolve the configured Agent Host from application state."""

    host = getattr(request.app.state, "agent_host", None)

    if host is None:
        raise AgentHostUnavailableError(
            "The Application Agent Runtime host is not configured"
        )

    return host
