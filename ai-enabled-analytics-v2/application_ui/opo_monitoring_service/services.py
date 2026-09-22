"""OPO-specific domain logic: KPI trend synthesis, outlier detection, wafer scoring.

Ported from the original demonstrator's ``services.py``. Per PLAN.md Phase 3 and the
target architecture's BFF boundary: functions reachable from ``agent_runtime/graph.py``
(the agent runtime) go through ``mcp_capability_adaptor.client`` - the only path from
the agent runtime to Foundation APIs. Functions that only back the plain (non-agent)
display route call ``foundation.clients`` directly, since the BFF may talk to
Foundation APIs itself for plain display with no agent or MCP involvement. Either way,
this module owns only the business interpretation of that data.
"""

from datetime import date, datetime, timedelta
from statistics import median
from typing import Any

from foundation.clients import lanadb_query as _foundation_lanadb
from mcp_capability_adaptor import client as mcp_client


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


def _build_trend_series(
    rows: list[dict[str, Any]],
    days: int | None,
    start_date: str | None,
    end_date: str | None,
    lot_ids: list[str] | None,
    product_ids: list[str] | None,
    layer_ids: list[str] | None,
    exposure_equipment_ids: list[str] | None,
) -> list[dict[str, Any]]:
    """Group/filter raw trend rows into per-machine/product point series. No outlier judgement.

    Either an explicit ``start_date``/``end_date`` range or a relative ``days``
    lookback applies - never both; the explicit range wins when given.
    """
    if start_date or end_date:
        range_start = date.fromisoformat(start_date) if start_date else date.min
        range_end = date.fromisoformat(end_date) if end_date else date.max
    elif days is not None:
        range_start = date.today() - timedelta(days=days - 1)
        range_end = date.max
    else:
        range_start = date.min
        range_end = date.max

    lot_id_set = {lot.lower() for lot in lot_ids} if lot_ids else None
    product_id_set = {p.lower() for p in product_ids} if product_ids else None
    layer_id_set = {layer.lower() for layer in layer_ids} if layer_ids else None
    exposure_equipment_id_set = {e.lower() for e in exposure_equipment_ids} if exposure_equipment_ids else None

    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for item in rows:
        machine, product = _coerce_series_identity(item)
        if exposure_equipment_id_set and machine.lower() not in exposure_equipment_id_set:
            continue
        if lot_id_set and str(item.get("lotId", item.get("lot_id", ""))).lower() not in lot_id_set:
            continue
        if product_id_set and product.lower() not in product_id_set:
            continue
        if layer_id_set and str(item.get("layerId", item.get("layer_id", ""))).lower() not in layer_id_set:
            continue

        point_timestamp = _coerce_point_timestamp(item.get("lotStart", item.get("lot_start")))
        kpi_value = item.get("kpiValue1", item.get("kpi_value"))
        if point_timestamp is None or kpi_value is None:
            continue
        point_date = point_timestamp.date()
        if point_date < range_start or point_date > range_end:
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


def get_trend_series(
    days: int | None = 14,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Trend series for the agent-runtime path: reads via MCP (the only path allowed
    from ``agent_runtime``/``graph.py`` to Foundation APIs)."""
    return _build_trend_series(
        mcp_client.read_trends(), days, start_date, end_date, lot_ids, product_ids, layer_ids, exposure_equipment_ids
    )


def get_display_trend_series(
    days: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Trend series for the plain (non-agent) BFF display route. Per the target
    architecture, the app UI/BFF may call the Foundation trend API directly - no
    agent or MCP involvement - for plain display (e.g. ``GET /trends``)."""
    return _build_trend_series(
        _foundation_lanadb.query_trend_rows(),
        days, start_date, end_date, lot_ids, product_ids, layer_ids, exposure_equipment_ids,
    )


def get_kpi_threshold_context(
    days: int | None = 14,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Empirical absolute KPI cutoffs (p95/p99/bell-curve spread) for model-supported
    suggestions. Computed by the MCP capability adaptor directly against the trend
    table, so only this small summary - not the full row set - crosses into the
    application layer.
    """
    return mcp_client.get_kpi_distribution_stats(
        days=days,
        start_date=start_date,
        end_date=end_date,
        lot_ids=lot_ids,
        product_ids=product_ids,
        layer_ids=layer_ids,
        exposure_equipment_ids=exposure_equipment_ids,
    )


def analyse_series(
    mode: str = "baseline",
    limit_value: float | None = None,
    direction: str = "below",
    baseline_deviation_pct: float = 3.0,
    limit_unit: str = "percent",
    days: int | None = 14,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
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
        start_date=start_date,
        end_date=end_date,
        lot_ids=lot_ids,
        product_ids=product_ids,
        layer_ids=layer_ids,
        exposure_equipment_ids=exposure_equipment_ids,
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


def _wafer_point_radius(row: dict[str, Any]) -> float:
    """Distance from wafer center, in the same field-center + intrafield-position
    coordinate system the UI's wafer map uses (see PLAN.md wafer-coordinate note)."""
    x = (
        row.get("exposureprocessjob_waferexposureprocessjob_exposurelogicalwafer_exposedfield_field_center_x", 0.0)
        or 0.0
    ) + (
        row.get("measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_x", row.get("position_x", 0.0))
        or 0.0
    )
    y = (
        row.get("exposureprocessjob_waferexposureprocessjob_exposurelogicalwafer_exposedfield_field_center_y", 0.0)
        or 0.0
    ) + (
        row.get("measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_y", row.get("position_y", 0.0))
        or 0.0
    )
    return ((float(x) ** 2) + (float(y) ** 2)) ** 0.5


def classify_wafer_spatial_pattern(rows: list[dict[str, Any]], anomalous_wafer_ids: list[str]) -> dict[str, Any]:
    """Edge-vs-center classification of the anomalous wafers' point positions.

    A point at or beyond 70% of the widest observed radius (across every point in
    this query, not just the anomalous ones) counts as 'edge' - a common metrology
    convention for wafer-edge effects. Deterministic and code-only, matching the
    rest of this module: no model call is involved in classifying real coordinates.
    """
    all_radii = [_wafer_point_radius(r) for r in rows]
    wafer_radius = max(all_radii) if all_radii else 0.0
    edge_threshold = wafer_radius * 0.7

    anomalous_ids = set(anomalous_wafer_ids)
    anomalous_radii = [_wafer_point_radius(r) for r in rows if r.get("wafer_id") in anomalous_ids]

    if not anomalous_radii:
        return {
            "anomalous_point_count": 0,
            "edge_count": 0,
            "center_count": 0,
            "edge_fraction": None,
            "wafer_radius_estimate_um": round(wafer_radius, 3),
            "edge_threshold_um": round(edge_threshold, 3),
            "pattern": "no_data",
        }

    edge_count = sum(1 for r in anomalous_radii if r >= edge_threshold)
    center_count = len(anomalous_radii) - edge_count
    if edge_count > center_count:
        pattern = "edge-concentrated"
    elif center_count > edge_count:
        pattern = "center-concentrated"
    else:
        pattern = "mixed"

    return {
        "anomalous_point_count": len(anomalous_radii),
        "edge_count": edge_count,
        "center_count": center_count,
        "edge_fraction": round(edge_count / len(anomalous_radii), 3),
        "wafer_radius_estimate_um": round(wafer_radius, 3),
        "edge_threshold_um": round(edge_threshold, 3),
        "pattern": pattern,
    }

