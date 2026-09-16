"""OPO-specific domain logic: KPI trend synthesis, outlier detection, wafer scoring.

Ported from the original demonstrator's ``services.py``. Per PLAN.md Phase 3, this
module is now split cleanly: all raw data access is delegated to
``mcp_capability_adaptor.client`` (governed MCP tool calls); this module owns only
the business interpretation of that data, which is application-specific and not a
platform concern.
"""

from datetime import date, datetime, timedelta
from statistics import median
from typing import Any

from mcp_capability_adaptor import client as mcp_client


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 3)


def get_dataset_metadata() -> dict[str, Any]:
    return {**mcp_client.get_trend_table_metadata(), **mcp_client.get_wafer_table_metadata()}


def _coerce_series_identity(item: dict[str, Any]) -> tuple[str, str]:
    machine = (
        item.get("machine")
        or item.get("exposureEquipmentId")
        or item.get("machineId")
        or "UNKNOWN_MACHINE"
    )
    product = (
        item.get("product")
        or item.get("productId")
        or item.get("layerId")
        or "UNKNOWN_PRODUCT"
    )
    return str(machine), str(product)


def _coerce_point_timestamp(value: Any) -> datetime | None:
    """Parse a real lotStart timestamp (ISO string or datetime), keeping time-of-day."""
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


def get_trend_series(
    days: int = 14,
    machine_id: str | None = None,
    lot_id: str | None = None,
    product_id: str | None = None,
    layer_id: str | None = None,
    exposure_equipment_id: str | None = None,
) -> list[dict[str, Any]]:
    """Real historical KPI points per machine/product. Carries no judgement about outliers."""
    cutoff = date.today() - timedelta(days=days - 1)
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for item in mcp_client.read_trends():
        machine, product = _coerce_series_identity(item)
        if machine_id and machine.lower() != machine_id.lower():
            continue
        if lot_id and str(item.get("lotId", item.get("lot_id", ""))).lower() != lot_id.lower():
            continue
        if product_id and product.lower() != product_id.lower():
            continue
        if layer_id and str(item.get("layerId", item.get("layer_id", ""))).lower() != layer_id.lower():
            continue
        if exposure_equipment_id and str(item.get("exposureEquipmentId", "")).lower() != exposure_equipment_id.lower():
            continue

        point_timestamp = _coerce_point_timestamp(item.get("lotStart", item.get("lot_start")))
        kpi_value = item.get("kpiValue1", item.get("kpi_value"))
        if point_timestamp is None or point_timestamp.date() < cutoff or kpi_value is None:
            continue

        key = (machine, product)
        group = grouped.setdefault(
            key,
            {
                "machine": machine,
                "product": product,
                "lot_id": item.get("lotId", item.get("lot_id")),
                "layer_id": item.get("layerId", item.get("layer_id")),
                "exposure_equipment_id": item.get("exposureEquipmentId"),
                "points": [],
            },
        )
        group["points"].append({
            "date": point_timestamp.isoformat(),
            "kpi_value": round(float(kpi_value), 2),
            "lot_id": item.get("lotId", item.get("lot_id")),
        })

    series = list(grouped.values())
    for entry in series:
        entry["points"].sort(key=lambda p: p["date"])
    return series


def get_kpi_threshold_context(
    days: int = 14,
    machine_id: str | None = None,
    lot_id: str | None = None,
    product_id: str | None = None,
    layer_id: str | None = None,
    exposure_equipment_id: str | None = None,
) -> dict[str, Any]:
    """Calculate empirical absolute KPI cutoffs for model-supported suggestions."""
    series = get_trend_series(
        days=days,
        machine_id=machine_id,
        lot_id=lot_id,
        product_id=product_id,
        layer_id=layer_id,
        exposure_equipment_id=exposure_equipment_id,
    )
    values = [point["kpi_value"] for item in series for point in item["points"]]
    return {
        "metric": "OPO KPI",
        "unit": "absolute",
        "sample_count": len(values),
        "observed_min": round(min(values), 3) if values else None,
        "observed_max": round(max(values), 3) if values else None,
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
    }


def analyse_series(
    mode: str = "baseline",
    limit_value: float | None = None,
    direction: str = "below",
    baseline_deviation_pct: float = 3.0,
    limit_unit: str = "percent",
    days: int = 14,
    machine_id: str | None = None,
    lot_id: str | None = None,
    product_id: str | None = None,
    layer_id: str | None = None,
    exposure_equipment_id: str | None = None,
) -> list[dict[str, Any]]:
    """Per-series summary under one of two rules.

    'absolute' compares every series against one fixed KPI limit, which suits a spec
    threshold. 'baseline' compares each series against its own median, which catches a
    machine moving away from its own normal even if it never breaches spec.

    Every series is returned, including unflagged ones, so the caller can see which
    did not qualify.
    """
    analysis = []

    for s in get_trend_series(
        days=days,
        machine_id=machine_id,
        lot_id=lot_id,
        product_id=product_id,
        layer_id=layer_id,
        exposure_equipment_id=exposure_equipment_id,
    ):
        baseline = median(p["kpi_value"] for p in s["points"])

        if mode == "absolute":
            requested = float(limit_value)
            above = direction == "above"
            applied = requested
            if limit_unit == "percent":
                applied = baseline * (1 + requested / 100) if above else baseline * (1 - requested / 100)
            flagged = [
                (i, p) for i, p in enumerate(s["points"])
                if (p["kpi_value"] >= applied if above else p["kpi_value"] <= applied)
            ]
            values = [p["kpi_value"] for _, p in flagged]
            extreme = (max(values) if above else min(values)) if values else None
            extreme_kpi = max((p["kpi_value"] for _, p in flagged), default=None) if above else min((p["kpi_value"] for _, p in flagged), default=None)
        else:
            applied = baseline * (1 + baseline_deviation_pct / 100)
            flagged = [(i, p) for i, p in enumerate(s["points"]) if p["kpi_value"] >= applied]
            values = [p["kpi_value"] for _, p in flagged]
            extreme = max(values) if values else None
            extreme_kpi = max((p["kpi_value"] for _, p in flagged), default=None)

        analysis.append(
            {
                "machine": s["machine"],
                "product": s["product"],
                "baseline": round(baseline, 1),
                "limit_applied_value": round(applied, 2),
                "extreme_kpi_value": extreme_kpi,
                # Keep the most extreme lot for compatibility, but retain every flagged
                # lot so a deep-dive can inspect the complete selected outlier series.
                "extreme_lot_id": next((p.get("lot_id") for _, p in flagged if p["kpi_value"] == extreme), None) if extreme is not None else None,
                "outlier_lot_ids": list(dict.fromkeys(
                    p.get("lot_id") for _, p in flagged if p.get("lot_id")
                )),
                "deviation_pct": (
                    round(abs(extreme - baseline) / baseline * 100, 1)
                    if extreme is not None
                    else 0.0
                ),
                # Real series can have multiple points sharing the same timestamp (e.g.
                # several wafers from one lot), so pair each date with its point index -
                # a bare date string would ring every point sharing that timestamp.
                "outlier_dates": [f"{i}#{p['date']}" for i, p in flagged],
            }
        )

    return analysis


def detect_outliers(**kwargs: Any) -> list[dict[str, Any]]:
    """Only the series with matching points, largest deviation first."""
    flagged = [a for a in analyse_series(**kwargs) if a["outlier_dates"]]
    return sorted(flagged, key=lambda r: r["deviation_pct"], reverse=True)


def create_workspace() -> str:
    return mcp_client.create_workspace()


def add_filters(workspace_id: str, filters: dict[str, Any]) -> dict[str, Any]:
    return mcp_client.add_workspace_filters(workspace_id, filters)


def register(workspace_id: str, dataset: str, table: str, *, approved: bool = False) -> dict[str, Any]:
    # `approved` is enforced by the human-approval `interrupt()` gate in
    # agent_runtime.graph before this is called; the MCP tool itself is
    # unconditional here, matching the original demonstrator's registration stub.
    return mcp_client.register_dataset(workspace_id, dataset, table)


def _normalize_wafer_row(row: dict[str, Any]) -> dict[str, Any]:
    wafer_id = (
        row.get("exposureprocessjob_waferexposureprocessjob_waferid")
        or row.get("wafer_id")
        or row.get("waferId")
        or "UNKNOWN_WAFER"
    )
    lot_id = row.get("exposureprocessjob_lotid") or row.get("lot_id") or row.get("lotId")
    layer_id = row.get("measureprocessjob_layerid") or row.get("layer_id") or row.get("layerId")
    machine = (
        row.get("exposureprocessjob_equipment_equipmentid")
        or row.get("machine")
        or row.get("exposureEquipmentId")
        or "UNKNOWN_MACHINE"
    )

    overlay_x = float(row.get("overlay_x", row.get("overlay_um", 0.0)) or 0.0)
    overlay_y = float(row.get("overlay_y", row.get("alignment_um", 0.0)) or 0.0)
    valid_x = bool(row.get("overlay_valid_x", True))
    valid_y = bool(row.get("overlay_valid_y", True))

    overlay_magnitude = ((overlay_x ** 2) + (overlay_y ** 2)) ** 0.5
    normalized = dict(row)
    normalized.pop("overlay_um", None)
    normalized.pop("alignment_um", None)
    normalized.pop("defect_density", None)
    normalized.update(
        {
            "wafer_id": str(wafer_id),
            "lot_id": lot_id,
            "layer_id": layer_id,
            "machine": str(machine),
            "overlay_x_um": round(overlay_x, 4),
            "overlay_y_um": round(overlay_y, 4),
            "overlay_valid_x": valid_x,
            "overlay_valid_y": valid_y,
            "overlay_magnitude_um": round(overlay_magnitude, 4),
        }
    )
    return normalized


_RAW_FILTER_FIELDS = {
    "machine": ("exposureprocessjob_equipment_equipmentid", "machine", "exposureEquipmentId"),
    "lot_id": ("exposureprocessjob_lotid", "lot_id", "lotId"),
    "layer_id": ("measureprocessjob_layerid", "layer_id", "layerId"),
}


def _matches_raw_filters(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, candidates in _RAW_FILTER_FIELDS.items():
        value = filters.get(key)
        if not value:
            continue
        raw_value = next((row.get(c) for c in candidates if row.get(c) is not None), None)
        if str(raw_value or "").lower() != str(value).lower():
            return False
    lot_ids = filters.get("lot_ids")
    if lot_ids:
        raw_lot_id = next(
            (row.get(candidate) for candidate in _RAW_FILTER_FIELDS["lot_id"] if row.get(candidate) is not None),
            None,
        )
        allowed_lot_ids = {str(lot_id).lower() for lot_id in lot_ids}
        if str(raw_lot_id or "").lower() not in allowed_lot_ids:
            return False
    return True


def query_wafer_data(
    workspace_id: str,
    table: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    connection_info = None
    if workspace_id and workspace_id != "TREND_PREVIEW":
        connection_info = mcp_client.get_workspace_connection_info(workspace_id)
    filters = filters or {}

    # Filter on raw rows before the (relatively expensive) per-row normalization,
    # since the mocked JDBC read has no server-side filtering of its own.
    rows = [
        _normalize_wafer_row(row)
        for row in mcp_client.read_wafers(table=table, connection_info=connection_info)
        if _matches_raw_filters(row, filters)
    ]

    anomalous = [
        r["wafer_id"]
        for r in rows
        if r.get("overlay_valid_x", True) and r.get("overlay_valid_y", True) and r.get("overlay_magnitude_um", 0) > 0.20
    ]
    anomalous = list(dict.fromkeys(anomalous))
    return {
        "workspace_id": workspace_id,
        "table": table or get_dataset_metadata().get("wafer_table", "starrocks.overlay_wafer_points"),
        "rows": rows,
        "anomalous_wafers": anomalous,
    }
