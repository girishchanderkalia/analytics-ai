"""Data warehouse (StarRocks) query API client (platform capability).

Stands in for Analytics Foundation's StarRocks access to wafer-level analytical
tables. Returns rows exactly as the underlying table would, with no business
interpretation - that is the application's job.

Reads the same mock dataset as the original demonstrator
(``AnalyticsFoundation/mock_data/datawarehouse_wafers(.json|.json.gz)``) in place,
read-only, so v2 does not fork or duplicate the (large) dataset.
"""

from pathlib import Path
import gzip
import json
from typing import Any

_dataset_cache: dict[str, Any] | None = None
_MOCK_DATA_DIR = Path(__file__).parents[3] / "AnalyticsFoundation" / "mock_data"
DATA_FILE = _MOCK_DATA_DIR / "datawarehouse_wafers.json"
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
            # Decompress in-memory only; never write back into the original
            # AnalyticsFoundation/mock_data tree from v2.
            with gzip.open(DATA_FILE_GZ, "rb") as f:
                payload = json.loads(f.read().decode("utf-8"))
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
            ],
        ),
    }


def query_wafer_rows(table: str | None = None, connection_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Raw rows from the StarRocks wafer table. No filtering, no interpretation."""
    return list(_load_dataset().get("wafer_rows", []))
