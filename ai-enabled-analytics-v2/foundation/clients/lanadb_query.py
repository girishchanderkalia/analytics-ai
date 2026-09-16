"""LandaDB (PostgreSQL) query API client (platform capability).

Stands in for Analytics Foundation's PostgreSQL access to high-level KPI/trend
tables. Returns rows exactly as the underlying table would, with no business
interpretation - that is the application's job.

Reads the same mock dataset as the original demonstrator
(``AnalyticsFoundation/mock_data/lanadb_trend.json``) in place, read-only, so v2
does not fork or duplicate the dataset (see PLAN.md constraints).
"""

from pathlib import Path
from typing import Any

import json

_dataset_cache: dict[str, Any] | None = None
DATA_FILE = Path(__file__).parents[3] / "AnalyticsFoundation" / "mock_data" / "lanadb_trend.json"

_DEFAULT_DATASET = {
    "trend_table": "postgres.overlay_kpi_trend",
    "series": [],
}


def _load_dataset() -> dict[str, Any]:
    global _dataset_cache
    if _dataset_cache is not None:
        return _dataset_cache

    dataset = dict(_DEFAULT_DATASET)
    if DATA_FILE.exists():
        try:
            payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                dataset.update(payload)
        except (json.JSONDecodeError, OSError):
            pass

    _dataset_cache = dataset
    return dataset


def get_table_metadata() -> dict[str, Any]:
    """Expose the logical table/column mapping for the mocked trend/KPI table."""
    dataset = _load_dataset()
    return {
        "trend_table": dataset.get("trend_table", "postgres.overlay_kpi_trend"),
        "kpi_columns": dataset.get("kpi_columns", ["kpiValue1", "kpiValue2"]),
        "query_projection": dataset.get(
            "query_projection",
            [
                "productId",
                "lotId",
                "layerId",
                "waferId",
                "measureProcessJobId",
                "exposureEquipmentId",
                "measurementEquipmentId",
                "lotStart",
                "kpiValue1",
                "kpiValue2",
                "needsIngestion",
            ],
        ),
    }


def _jdbc_get(connection_info: dict[str, Any] | None, table: str | None) -> list[dict[str, Any]]:
    """Mocked JDBC GET: a real deployment issues ``SELECT * FROM {table}`` over ``connection_info``."""
    return list(_load_dataset().get("series", []))


def query_trend_rows(table: str | None = None, connection_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Raw rows from the PostgreSQL trend/KPI table. No filtering, no interpretation."""
    return _jdbc_get(connection_info, table)
