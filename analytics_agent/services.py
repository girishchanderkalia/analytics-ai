"""Stubs standing in for Analytics Foundation services.

Each function maps to a platform API that will replace it: trends to PostgreSQL,
workspace/registration to the Workspace API, wafer queries to the Query Engine.
"""

import uuid
from typing import Any

_registration_attempts: dict[str, int] = {}


def get_trends() -> list[dict[str, Any]]:
    return [
        {"machine": "NXE3600", "product": "ProductA", "yield_degradation": 15.0},
        {"machine": "NXE3400", "product": "ProductB", "yield_degradation": 8.5},
        {"machine": "NXT1970", "product": "ProductC", "yield_degradation": 4.2},
    ]


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


def query_wafer_data(workspace_id: str, table: str) -> dict[str, Any]:
    rows = [
        {"wafer_id": "W001", "yield_pct": 72.3, "defect_density": 0.42},
        {"wafer_id": "W002", "yield_pct": 69.1, "defect_density": 0.51},
        {"wafer_id": "W003", "yield_pct": 71.8, "defect_density": 0.44},
        {"wafer_id": "W004", "yield_pct": 55.2, "defect_density": 1.23},
        {"wafer_id": "W005", "yield_pct": 56.0, "defect_density": 1.18},
    ]
    anomalous = [r["wafer_id"] for r in rows if r["defect_density"] > 1.0]
    return {
        "workspace_id": workspace_id,
        "table": table,
        "rows": rows,
        "anomalous_wafers": anomalous,
    }
