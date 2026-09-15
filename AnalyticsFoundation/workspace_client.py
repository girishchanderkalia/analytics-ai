"""Workspace API client (platform capability).

Stands in for Analytics Foundation's Workspace API: create a workspace, apply
filters to it, register a dataset/table for querying, and hand out the JDBC
connection info for the workspace's provisioned database. Backed by an in-memory
stub today; a real deployment would call the endpoints in ``apis/api.yml`` instead,
with row-level access then made over JDBC using ``get_connection_info`` against a
database provisioned via the Query Engine Database API (``apis/qe_api.yml``).
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


def get_connection_info(workspace_id: str) -> dict[str, Any]:
    """Mocked JDBC connection info for the workspace's provisioned database.

    Real deployment: GET /v2/workspaces/{id}/connection-info (apis/api.yml), returning
    a WorkspaceConnectionInfo (databaseEndpoint, userName, password) for a JDBC client
    to reach the PostgreSQL/StarRocks database created via the Query Engine API.
    """
    return {
        "databaseEndpoint": f"mock-query-engine.workspace-{workspace_id}.svc.cluster.local:9030",
        "userName": f"user_{workspace_id.lower()}",
        "password": f"pw_{uuid.uuid4().hex[:12]}",
    }
