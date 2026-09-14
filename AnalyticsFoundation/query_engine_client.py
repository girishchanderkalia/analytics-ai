"""Query Engine API client (platform capability).

Stands in for Analytics Foundation's Query Engine: raw row access to PostgreSQL
(KPI/trend tables) and StarRocks (wafer-level tables). Returns rows exactly as the
underlying tables would, with no business interpretation - that is the
application's job. Backed by a local mock data file today; a real deployment would
call the endpoints in ``apis/qe_api.yml`` instead.
"""

import json
import math
from pathlib import Path
from typing import Any

_dataset_cache: dict[str, Any] | None = None
DATA_FILE = Path(__file__).resolve().with_name("mock_data") / "opo_dataset.json"

_DEFAULT_DATASET = {
    "trend_table": "postgres.overlay_kpi_trend",
    "series": [],
    "wafer_table": "starrocks.overlay_wafer_points",
    "wafer_rows": [],
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
    """Expose the logical table/column mapping for the mocked data source."""
    dataset = _load_dataset()
    return {
        "trend_table": dataset.get("trend_table", "postgres.overlay_kpi_trend"),
        "wafer_table": dataset.get("wafer_table", "starrocks.overlay_wafer_points"),
        "kpi_columns": dataset.get("kpi_columns", ["kpiValue1", "kpiValue2"]),
        "wafer_columns": dataset.get(
            "wafer_columns",
            [
                "field_center_x",
                "field_center_y",
                "position_x",
                "position_y",
                "image_width",
                "image_height",
                "overlay_x",
                "overlay_y",
                "overlay_valid_x",
                "overlay_valid_y",
                "lotId",
                "waferId",
                "chuck_id",
                "layerId",
                "equipmentId",
            ],
        ),
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


def query_trend_rows(table: str | None = None) -> list[dict[str, Any]]:
    """Raw rows from the PostgreSQL trend/KPI table. No filtering, no interpretation."""
    return list(_load_dataset().get("series", []))


def _generate_default_wafer_rows() -> list[dict[str, Any]]:
    """Synthetic StarRocks rows used when the mock dataset has none, in native schema."""
    wafers = [
        ("W001", "LOT-1041", "LAYER-01", "NXE3600", 0.12),
        ("W002", "LOT-1042", "LAYER-01", "NXE3400", 0.15),
        ("W003", "LOT-2041", "LAYER-02", "NXT1970", 0.10),
    ]
    rows: list[dict[str, Any]] = []
    for wafer_id, lot_id, layer_id, machine, base_scale in wafers:
        for idx in range(32):
            angle = (idx / 32) * (2 * math.pi)
            radius = 0.45 + ((idx % 7) * 0.03)
            px = radius * 2.3 * math.cos(angle)
            py = radius * 2.1 * math.sin(angle)
            overlay_x = round((px / 70.0) * base_scale, 4)
            overlay_y = round((py / 70.0) * base_scale, 4)
            rows.append(
                {
                    "exposureprocessjob_waferexposureprocessjob_exposurelogicalwafer_exposedfield_field_center_x": 0.0,
                    "exposureprocessjob_waferexposureprocessjob_exposurelogicalwafer_exposedfield_field_center_y": 0.0,
                    "measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_x": round(px, 4),
                    "measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_y": round(py, 4),
                    "exposureprocessjob_reticle_image_imagesize_width": 1200,
                    "exposureprocessjob_reticle_image_imagesize_height": 1200,
                    "overlay_x": overlay_x,
                    "overlay_y": overlay_y,
                    "overlay_valid_x": True,
                    "overlay_valid_y": True,
                    "exposureprocessjob_lotid": lot_id,
                    "exposureprocessjob_waferexposureprocessjob_waferid": wafer_id,
                    "exposureprocessjob_waferexposureprocessjob_chuck_id": f"CHUCK-{idx % 5 + 1}",
                    "measureprocessjob_layerid": layer_id,
                    "exposureprocessjob_equipment_equipmentid": machine,
                }
            )

    for idx in range(8):
        wafer_id = f"W00{idx + 4}"
        lot_id = f"LOT-{2050 + idx}"
        layer_id = "LAYER-02"
        machine = "NXE3600" if idx % 2 == 0 else "NXE3400"
        radius = 0.5 + (idx * 0.05)
        for point_idx in range(24):
            angle = (point_idx / 24) * (2 * math.pi)
            px = radius * 2.3 * math.cos(angle)
            py = radius * 2.1 * math.sin(angle)
            overlay_x = round((px / 70.0) * 0.28, 4)
            overlay_y = round((py / 70.0) * 0.21, 4)
            rows.append(
                {
                    "exposureprocessjob_waferexposureprocessjob_exposurelogicalwafer_exposedfield_field_center_x": 0.0,
                    "exposureprocessjob_waferexposureprocessjob_exposurelogicalwafer_exposedfield_field_center_y": 0.0,
                    "measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_x": round(px, 4),
                    "measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_y": round(py, 4),
                    "exposureprocessjob_reticle_image_imagesize_width": 1200,
                    "exposureprocessjob_reticle_image_imagesize_height": 1200,
                    "overlay_x": overlay_x,
                    "overlay_y": overlay_y,
                    "overlay_valid_x": True,
                    "overlay_valid_y": True,
                    "exposureprocessjob_lotid": lot_id,
                    "exposureprocessjob_waferexposureprocessjob_waferid": wafer_id,
                    "exposureprocessjob_waferexposureprocessjob_chuck_id": f"CHUCK-{idx % 6 + 1}",
                    "measureprocessjob_layerid": layer_id,
                    "exposureprocessjob_equipment_equipmentid": machine,
                }
            )
    return rows


def query_wafer_rows(table: str | None = None) -> list[dict[str, Any]]:
    """Raw rows from the StarRocks wafer table. No filtering, no interpretation."""
    rows = list(_load_dataset().get("wafer_rows", []))
    return rows if rows else _generate_default_wafer_rows()
