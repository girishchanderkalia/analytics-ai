"""Workspace API client (platform capability).

Stands in for Analytics Foundation's Workspace API: create a workspace, apply
filters to it, and register a dataset/table for querying. Backed by an in-memory
stub today; a real deployment would call the endpoints in ``apis/api.yml`` instead.
"""

import uuid
from typing import Any

_registration_attempts: dict[str, int] = {}


def create_workspace() -> str:
    return f"WS-{uuid.uuid4().hex[:8].upper()}"


def add_filters(workspace_id: str, filters: dict[str, Any]) -> dict[str, Any]:
    return {"workspace_id": workspace_id, "filters": filters}


def register(workspace_id: str, dataset: str, table: str) -> dict[str, Any]:
    """Registration is asynchronous upstream; progress is simulated over repeated calls."""
    attempts = _registration_attempts.get(workspace_id, 0) + 1
    _registration_attempts[workspace_id] = attempts

    if attempts < 3:
        return {
            "status": "IN_PROGRESS",
            "workspace_id": workspace_id,
            "progress_pct": attempts * 33,
            "table": table,
        }
    return {
        "status": "READY",
        "workspace_id": workspace_id,
        "progress_pct": 100,
        "table": table,
    }
