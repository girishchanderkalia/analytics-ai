"""Immutable request, result, and cache models for the central runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from .runtime_errors import AgentRuntimeError


class AgentRuntimeStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, order=True)
class CompiledGraphKey:
    application_id: str
    agent_id: str
    version: str
    definition_fingerprint: str

    def __post_init__(self) -> None:
        for field_name in (
            "application_id",
            "agent_id",
            "version",
            "definition_fingerprint",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True)
class AgentRuntimeStartRequest:
    application_id: str
    agent_id: str
    version: str
    thread_id: str
    initial_state: Mapping[str, Any]

    def __post_init__(self) -> None:
        for field_name in (
            "application_id",
            "agent_id",
            "version",
            "thread_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )
        if not isinstance(self.initial_state, Mapping):
            raise AgentRuntimeError("initial_state must be a mapping")
        object.__setattr__(self, "initial_state", dict(self.initial_state))


@dataclass(frozen=True)
class AgentRuntimeStateRequest:
    application_id: str
    agent_id: str
    version: str
    thread_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "application_id",
            "agent_id",
            "version",
            "thread_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True)
class AgentRuntimeResult:
    application_id: str
    agent_id: str
    version: str
    thread_id: str
    state: Mapping[str, Any]
    status: AgentRuntimeStatus = AgentRuntimeStatus.COMPLETED

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", dict(self.state))


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentRuntimeError(f"{field_name} must be a non-empty string")
    return value.strip()
