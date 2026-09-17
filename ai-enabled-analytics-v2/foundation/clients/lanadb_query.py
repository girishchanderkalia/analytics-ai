"""LandaDB (PostgreSQL) query API client (platform capability).

Stands in for Analytics Foundation's PostgreSQL access to high-level KPI/trend
tables. Returns rows exactly as the underlying table would, with no business
interpretation - that is the application's job.

Reads the same mock dataset as the original demonstrator
(``AnalyticsFoundation/mock_data/lanadb_trend.json``) in place, read-only, so v2
does not fork or duplicate the dataset (see PLAN.md constraints).
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean as _mean
from statistics import pstdev
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


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 3)


def _row_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_kpi_distribution_stats(
    days: int | None = 14,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Deterministic p95/p99/mean/spread stats computed next to the data.

    Mirrors what a real deployment would push down as
    ``SELECT PERCENTILE_CONT(...), STDDEV(...) FROM trend_table WHERE ...``: the
    filtering and math happen here, at the source, so only a small summary - not the
    full row set - ever crosses the MCP tool boundary into the application layer.
    """
    if start_date or end_date:
        range_start = date.fromisoformat(start_date) if start_date else date.min
        range_end = date.fromisoformat(end_date) if end_date else date.max
    else:
        range_start = date.today() - timedelta(days=(days or 14) - 1)
        range_end = date.max

    lot_id_set = {lot.lower() for lot in lot_ids} if lot_ids else None
    product_id_set = {p.lower() for p in product_ids} if product_ids else None
    layer_id_set = {layer.lower() for layer in layer_ids} if layer_ids else None
    exposure_equipment_id_set = {e.lower() for e in exposure_equipment_ids} if exposure_equipment_ids else None

    values: list[float] = []

    for item in _load_dataset().get("series", []):
        machine = str(
            item.get("exposureEquipmentId") or item.get("machine") or item.get("machineId") or "UNKNOWN_MACHINE"
        )
        product = str(item.get("productId") or item.get("product") or item.get("layerId") or "UNKNOWN_PRODUCT")
        if exposure_equipment_id_set and machine.lower() not in exposure_equipment_id_set:
            continue
        if product_id_set and product.lower() not in product_id_set:
            continue
        if lot_id_set and str(item.get("lotId", item.get("lot_id", ""))).lower() not in lot_id_set:
            continue
        if layer_id_set and str(item.get("layerId", item.get("layer_id", ""))).lower() not in layer_id_set:
            continue

        timestamp = _row_timestamp(item.get("lotStart", item.get("lot_start")))
        kpi_value = item.get("kpiValue1", item.get("kpi_value"))
        if timestamp is None or kpi_value is None:
            continue
        point_date = timestamp.date()
        if point_date < range_start or point_date > range_end:
            continue
        values.append(float(kpi_value))

    if not values:
        return {
            "metric": "OPO KPI",
            "unit": "absolute",
            "sample_count": 0,
            "observed_min": None,
            "observed_max": None,
            "mean": None,
            "stdev": None,
            "p95": None,
            "p99": None,
            "bell_curve_range": None,
        }

    ordered = sorted(values)
    avg = round(_mean(values), 3)
    spread = round(pstdev(values), 3) if len(values) > 1 else 0.0
    return {
        "metric": "OPO KPI",
        "unit": "absolute",
        "sample_count": len(values),
        "observed_min": round(ordered[0], 3),
        "observed_max": round(ordered[-1], 3),
        "mean": avg,
        "stdev": spread,
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
        # +/-2 stdev covers ~95% of a normal ("bell curve") distribution, giving the
        # model a spread-based band alongside the raw percentile cutoffs.
        "bell_curve_range": [round(avg - 2 * spread, 3), round(avg + 2 * spread, 3)],
    }
