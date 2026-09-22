"""Translate runtime-domain exceptions to stable HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from catalog.catalog_models import AgentCatalogError, AgentNotFoundError
from execution.execution_models import ApprovalResumeError, WorkflowExecutionError

from .dependencies import AgentHostUnavailableError


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict] | None = None,
) -> JSONResponse:
    """Create the common error envelope."""

    body: dict = {
        "error": {
            "code": code,
            "message": message,
        }
    }

    if details is not None:
        body["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=body,
    )


def install_error_handlers(app: FastAPI) -> None:
    """Register runtime API exception mappings."""

    @app.exception_handler(AgentNotFoundError)
    async def handle_agent_not_found(
        request: Request,
        exc: AgentNotFoundError,
    ) -> JSONResponse:
        del request
        return error_response(404, "agent_not_found", str(exc))

    @app.exception_handler(ApprovalResumeError)
    async def handle_approval_resume(
        request: Request,
        exc: ApprovalResumeError,
    ) -> JSONResponse:
        del request
        return error_response(409, "approval_resume_rejected", str(exc))

    @app.exception_handler(WorkflowExecutionError)
    async def handle_workflow_execution(
        request: Request,
        exc: WorkflowExecutionError,
    ) -> JSONResponse:
        del request
        return error_response(422, "workflow_execution_rejected", str(exc))

    @app.exception_handler(AgentCatalogError)
    async def handle_catalog_error(
        request: Request,
        exc: AgentCatalogError,
    ) -> JSONResponse:
        del request
        return error_response(400, "agent_catalog_error", str(exc))

    @app.exception_handler(AgentHostUnavailableError)
    async def handle_missing_host(
        request: Request,
        exc: AgentHostUnavailableError,
    ) -> JSONResponse:
        del request
        return error_response(503, "agent_host_unavailable", str(exc))

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        del request
        details = [
            {
                "location": list(error.get("loc", ())),
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "validation_error"),
            }
            for error in exc.errors()
        ]
        return error_response(
            422,
            "request_validation_error",
            "The request payload is invalid",
            details,
        )
