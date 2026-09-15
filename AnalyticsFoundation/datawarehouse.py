"""Data warehouse (StarRocks) query API client (platform capability).

Stands in for Analytics Foundation's StarRocks access to wafer-level analytical
tables. Returns rows exactly as the underlying table would, with no business
interpretation - that is the application's job.

Row-level reads are a JDBC connection using credentials from the Workspace API's
connection-info endpoint (``workspace_client.get_connection_info``) against a
database provisioned via the Query Engine API (``query_engine_client``, backed by
``apis/qe_api.yml``). ``_jdbc_get`` mocks that JDBC call as a simple GET over a
local mock data file; swap it for a real driver to connect live.
"""

import math
from pathlib import Path
import gzip
import json
from typing import Any

_dataset_cache: dict[str, Any] | None = None
DATA_FILE = Path(__file__).with_name("mock_data") / "datawarehouse_wafers.json"
DATA_FILE_GZ = DATA_FILE.with_suffix(DATA_FILE.suffix + ".gz")

_DEFAULT_DATASET = {
    "wafer_table": "starrocks.overlay_wafer_points",
    "wafer_rows": [],
}


def _load_dataset() -> dict[str, Any]:
    global _dataset_cache
    if _dataset_cache is not None:
        return _dataset_cache

    dataset = dict(_DEFAULT_DATASET)
    payload = None
    try:
        if DATA_FILE.exists():
            payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        elif DATA_FILE_GZ.exists():
            # Committed dataset is gzipped (see run.sh); unpack once and persist to
            # disk so later process starts hit the plain-file fast path above instead
            # of re-decompressing every time.
            with gzip.open(DATA_FILE_GZ, "rb") as f:
                raw_bytes = f.read()
            try:
                DATA_FILE.write_bytes(raw_bytes)
            except OSError:
                pass
            payload = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, OSError):
        payload = None

    if isinstance(payload, dict):
        dataset.update(payload)

    _dataset_cache = dataset
    return dataset


def get_table_metadata() -> dict[str, Any]:
    """Expose the logical table/column mapping for the mocked wafer table."""
    dataset = _load_dataset()
    return {
        "wafer_table": dataset.get("wafer_table", "starrocks.overlay_wafer_points"),
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
    }


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


def _jdbc_get(connection_info: dict[str, Any] | None, table: str | None) -> list[dict[str, Any]]:
    """Mocked JDBC GET: a real deployment issues ``SELECT * FROM {table}`` over ``connection_info``."""
    rows = list(_load_dataset().get("wafer_rows", []))
    return rows if rows else _generate_default_wafer_rows()


def query_wafer_rows(table: str | None = None, connection_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Raw rows from the StarRocks wafer table. No filtering, no interpretation."""
    return _jdbc_get(connection_info, table)
