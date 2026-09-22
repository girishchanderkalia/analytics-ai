"""FastAPI application factory for the persisted Runtime Service."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from .error_mapping import install_error_handlers
from .routes import router


def create_app(runtime_service: Any | None = None) -> FastAPI:
    """Create a FastAPI app and inject the persisted Runtime Service."""

    app = FastAPI(
        title="Application Agent Runtime API",
        version="2.0.0",
        description=(
            "Start, resume, and inspect durable application-agent conversations."
        ),
    )

    app.state.runtime_service = runtime_service
    install_error_handlers(app)
    app.include_router(router)

    return app
