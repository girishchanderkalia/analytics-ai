"""Pydantic transport models for the Application Agent Runtime API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictApiModel(BaseModel):
    """Base model that rejects undeclared transport fields."""

    model_config = ConfigDict(extra="forbid")


class StartExecutionRequest(StrictApiModel):
    """Request to start a new agent workflow execution."""

    version: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)


class ResumeExecutionRequest(StrictApiModel):
    """Request to resume an interrupted approval node."""

    version: str | None = None
    state: dict[str, Any]
    current_node: str = Field(min_length=1)
    approved: bool
    selected_outlier_id: str | None = None
    comment: str | None = None
    values: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequestResponse(BaseModel):
    """Approval details returned to an API consumer."""

    model_config = ConfigDict(extra="allow")

    approval_id: str | None = None
    node_id: str | None = None
    public_type: str | None = None


class ExecutionResponse(BaseModel):
    """Stable transport representation of a hosted execution result."""

    agent_id: str
    agent_version: str
    status: str
    state: dict[str, Any]
    current_node: str | None = None
    approval_request: ApprovalRequestResponse | None = None
    error: str | None = None


class AgentCatalogItemResponse(BaseModel):
    """Public metadata for one catalog entry."""

    agent_id: str
    version: str
    display_name: str
    directory_name: str
    agent_directory: str


class AgentCatalogResponse(BaseModel):
    """List of agents available to the runtime API."""

    agents: list[AgentCatalogItemResponse]


class HealthResponse(BaseModel):
    """Minimal liveness response."""

    status: str


class ApiErrorDetail(BaseModel):
    """Machine-readable API error detail."""

    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ApiErrorResponse(BaseModel):
    """Common error response envelope."""

    error: ApiErrorDetail
