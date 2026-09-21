"""HTTP routes for catalog, start, and resume operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from execution.execution_models import ResumeInput

from .dependencies import get_agent_host
from .models import (
    AgentCatalogResponse,
    ExecutionResponse,
    HealthResponse,
    ResumeExecutionRequest,
    StartExecutionRequest,
)
from .serialization import execution_response


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
)
def health() -> HealthResponse:
    """Return a minimal liveness response."""

    return HealthResponse(status="ok")


@router.get(
    "/v1/agents",
    response_model=AgentCatalogResponse,
    tags=["agents"],
)
def list_agents(
    host: Any = Depends(get_agent_host),
) -> AgentCatalogResponse:
    """List the agents available through the configured catalog."""

    return AgentCatalogResponse(
        agents=host.catalog.list()
    )


@router.post(
    "/v1/agents/{agent_id}/executions",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    tags=["executions"],
)
def start_execution(
    agent_id: str,
    request: StartExecutionRequest,
    host: Any = Depends(get_agent_host),
) -> ExecutionResponse:
    """Start a new workflow execution."""

    hosted_result = host.start(
        agent_id=agent_id,
        initial_state=request.state,
        version=request.version,
    )

    return execution_response(hosted_result)


@router.post(
    "/v1/agents/{agent_id}/executions/resume",
    response_model=ExecutionResponse,
    tags=["executions"],
)
def resume_execution(
    agent_id: str,
    request: ResumeExecutionRequest,
    host: Any = Depends(get_agent_host),
) -> ExecutionResponse:
    """Resume a workflow paused at an approval node."""

    resume_input = ResumeInput(
        approved=request.approved,
        selected_outlier_id=request.selected_outlier_id,
        comment=request.comment,
        values=request.values,
    )

    hosted_result = host.resume(
        agent_id=agent_id,
        state=request.state,
        current_node=request.current_node,
        resume_input=resume_input,
        version=request.version,
    )

    return execution_response(hosted_result)
