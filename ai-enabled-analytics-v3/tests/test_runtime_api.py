"""FastAPI contract tests for the Application Agent Runtime API."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient


V3_ROOT = Path(__file__).resolve().parents[1]
AGENT_RUNTIME_ROOT = V3_ROOT / "agent-runtime"

if str(AGENT_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_RUNTIME_ROOT))


from catalog.catalog_models import AgentNotFoundError  # noqa: E402
from runtime_api import create_app  # noqa: E402


class FakeStatus(StrEnum):
    COMPLETED = "completed"
    WAITING = "waiting_for_approval"


@dataclass(frozen=True)
class FakeApprovalRequest:
    approval_id: str
    node_id: str
    public_type: str


class FakeCatalog:
    def list(self) -> list[dict[str, str]]:
        return [
            {
                "agent_id": "opo-monitoring-agent",
                "version": "1.0",
                "display_name": "OPO Monitoring Agent",
                "directory_name": "opo-monitoring",
                "agent_directory": "ai-agents/opo-monitoring",
            }
        ]


class FakeHost:
    def __init__(self) -> None:
        self.catalog = FakeCatalog()
        self.start_calls: list[dict[str, Any]] = []
        self.resume_calls: list[dict[str, Any]] = []

    def start(
        self,
        agent_id: str,
        initial_state: dict[str, Any],
        version: str | None = None,
    ) -> Any:
        if agent_id == "unknown-agent":
            raise AgentNotFoundError("Agent is not available: unknown-agent")

        self.start_calls.append(
            {
                "agent_id": agent_id,
                "initial_state": initial_state,
                "version": version,
            }
        )

        result = SimpleNamespace(
            status=FakeStatus.COMPLETED,
            state={**initial_state, "status": "completed"},
            current_node=None,
            approval_request=None,
            error=None,
        )

        return SimpleNamespace(
            agent_id=agent_id,
            agent_version=version or "1.0",
            result=result,
        )

    def resume(
        self,
        agent_id: str,
        state: dict[str, Any],
        current_node: str,
        resume_input: Any,
        version: str | None = None,
    ) -> Any:
        self.resume_calls.append(
            {
                "agent_id": agent_id,
                "state": state,
                "current_node": current_node,
                "resume_input": resume_input,
                "version": version,
            }
        )

        result = SimpleNamespace(
            status=FakeStatus.COMPLETED,
            state={**state, "status": "completed"},
            current_node=None,
            approval_request=None,
            error=None,
        )

        return SimpleNamespace(
            agent_id=agent_id,
            agent_version=version or "1.0",
            result=result,
        )


def test_health_endpoint() -> None:
    client = TestClient(create_app(FakeHost()))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_agents_endpoint() -> None:
    client = TestClient(create_app(FakeHost()))
    response = client.get("/v1/agents")
    assert response.status_code == 200
    assert response.json()["agents"][0]["agent_id"] == "opo-monitoring-agent"


def test_start_execution_endpoint() -> None:
    host = FakeHost()
    client = TestClient(create_app(host))
    response = client.post(
        "/v1/agents/opo-monitoring-agent/executions",
        json={
            "version": "1.0",
            "state": {"question": "Show trends"},
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert host.start_calls[0]["initial_state"] == {"question": "Show trends"}


def test_resume_execution_endpoint() -> None:
    host = FakeHost()
    client = TestClient(create_app(host))
    response = client.post(
        "/v1/agents/opo-monitoring-agent/executions/resume",
        json={
            "version": "1.0",
            "state": {"status": "waiting_for_approval"},
            "current_node": "approve_investigation",
            "approved": True,
            "selected_outlier_id": "outlier-1",
            "comment": "Proceed",
            "values": {},
        },
    )
    assert response.status_code == 200
    call = host.resume_calls[0]
    assert call["resume_input"].approved is True
    assert call["resume_input"].selected_outlier_id == "outlier-1"


def test_agent_not_found_is_mapped_to_404() -> None:
    client = TestClient(create_app(FakeHost()))
    response = client.post(
        "/v1/agents/unknown-agent/executions",
        json={"state": {}},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "agent_not_found"


def test_invalid_request_is_mapped_to_common_error() -> None:
    client = TestClient(create_app(FakeHost()))
    response = client.post(
        "/v1/agents/opo-monitoring-agent/executions/resume",
        json={
            "state": {},
            "current_node": "",
            "approved": True,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


def test_missing_host_is_mapped_to_503() -> None:
    client = TestClient(create_app())
    response = client.get("/v1/agents")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "agent_host_unavailable"
