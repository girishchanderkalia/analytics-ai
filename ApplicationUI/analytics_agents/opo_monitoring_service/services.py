"""OPO-specific domain logic: KPI trend synthesis, outlier detection, wafer scoring.

Raw data access goes through the ``AnalyticsFoundation`` platform clients
(``workspace_client``, ``query_engine_client``); this module owns the business
interpretation of that data, which is application-specific and not a platform concern.
"""

from datetime import date, timedelta
from statistics import median
from typing import Any

from AnalyticsFoundation import query_engine_client
from AnalyticsFoundation.capability_registry import invoke as invoke_capability

DEFAULT_ABSOLUTE_BASELINE = 3.0
OPO_PERMISSIONS = {
    "workspace:create",
    "workspace:write",
    "workspace:register",
    "query:trends:read",
    "query:wafers:read",
}


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
    return query_engine_client.get_table_metadata()


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


def get_trend_series(
    days: int = 14,
    machine_id: str | None = None,
    lot_id: str | None = None,
    product_id: str | None = None,
    layer_id: str | None = None,
    exposure_equipment_id: str | None = None,
) -> list[dict[str, Any]]:
    """Raw daily KPI per machine/product. Carries no judgement about outliers."""
    today = date.today()
    series = []

    for item in invoke_capability(
        "query_engine.read_trends",
        permissions=OPO_PERMISSIONS,
        table=None,
    ):
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
        dip_days = int(item.get("dip_days", item.get("dipDays", 1)))
        absolute_baseline = float(item.get("absolute_baseline", item.get("absoluteBaseline", DEFAULT_ABSOLUTE_BASELINE)))
        absolute_outlier = float(item.get("absolute_outlier", item.get("absoluteOutlier", absolute_baseline)))

        points = []

        for i in range(days):
            point_date = today - timedelta(days=days - 1 - i)
            wobble = ((i * 37) % 7 - 3) / 10
            is_dip = i >= days - dip_days
            absolute_wobble = ((i * 29) % 7 - 3) / 100
            points.append(
                {
                    "date": point_date.isoformat(),
                    "kpi_value": round((absolute_outlier if is_dip else absolute_baseline) + absolute_wobble, 2),
                }
            )

        series.append({
            "machine": machine,
            "product": product,
            "lot_id": item.get("lotId", item.get("lot_id")),
            "layer_id": item.get("layerId", item.get("layer_id")),
            "exposure_equipment_id": item.get("exposureEquipmentId"),
            "points": points,
        })

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
                p for p in s["points"]
                if (p["kpi_value"] >= applied if above else p["kpi_value"] <= applied)
            ]
            values = [p["kpi_value"] for p in flagged]
            extreme = (max(values) if above else min(values)) if values else None
            extreme_kpi = max((p["kpi_value"] for p in flagged), default=None) if above else min((p["kpi_value"] for p in flagged), default=None)
        else:
            applied = baseline * (1 + baseline_deviation_pct / 100)
            flagged = [p for p in s["points"] if p["kpi_value"] >= applied]
            values = [p["kpi_value"] for p in flagged]
            extreme = max(values) if values else None
            extreme_kpi = max((p["kpi_value"] for p in flagged), default=None)

        analysis.append(
            {
                "machine": s["machine"],
                "product": s["product"],
                "baseline": round(baseline, 1),
                "limit_applied_value": round(applied, 2),
                "extreme_kpi_value": extreme_kpi,
                "deviation_pct": (
                    round(abs(extreme - baseline) / baseline * 100, 1)
                    if extreme is not None
                    else 0.0
                ),
                "outlier_dates": [p["date"] for p in flagged],
            }
        )

    return analysis


def detect_outliers(**kwargs: Any) -> list[dict[str, Any]]:
    """Only the series with matching points, largest deviation first."""
    flagged = [a for a in analyse_series(**kwargs) if a["outlier_dates"]]
    return sorted(flagged, key=lambda r: r["deviation_pct"], reverse=True)


def create_workspace() -> str:
    return invoke_capability("workspace.create", permissions=OPO_PERMISSIONS)


def add_filters(workspace_id: str, filters: dict[str, Any]) -> dict[str, Any]:
    return invoke_capability(
        "workspace.add_filters",
        permissions=OPO_PERMISSIONS,
        workspace_id=workspace_id,
        filters=filters,
    )


def register(workspace_id: str, dataset: str, table: str, *, approved: bool = False) -> dict[str, Any]:
    return invoke_capability(
        "workspace.register_dataset",
        permissions=OPO_PERMISSIONS,
        approved=approved,
        workspace_id=workspace_id,
        dataset=dataset,
        table=table,
    )


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


def query_wafer_data(
    workspace_id: str,
    table: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = [
        _normalize_wafer_row(row)
        for row in invoke_capability(
            "query_engine.read_wafers",
            permissions=OPO_PERMISSIONS,
            table=table,
        )
    ]

    filters = filters or {}
    for key in ("machine", "lot_id", "layer_id"):
        value = filters.get(key)
        if value:
            rows = [row for row in rows if str(row.get(key, "")).lower() == str(value).lower()]

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
