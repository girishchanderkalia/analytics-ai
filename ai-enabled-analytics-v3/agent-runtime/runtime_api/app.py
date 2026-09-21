"""FastAPI application factory for the Application Agent Runtime."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from .error_mapping import install_error_handlers
from .routes import router


def create_app(agent_host: Any | None = None) -> FastAPI:
    """Create a FastAPI application with an optional Agent Host."""

    app = FastAPI(
        title="Application Agent Runtime API",
        version="1.0.0",
        description=(
            "Start and resume declarative application-agent workflows."
        ),
    )

    app.state.agent_host = agent_host
    install_error_handlers(app)
    app.include_router(router)

    return app
