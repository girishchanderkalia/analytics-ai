import json

import AnalyticsFoundation.query_engine_client as query_engine_client
from AnalyticsFoundation import session_memory
from AnalyticsFoundation.capability_registry import invoke, list_capabilities
import ApplicationUI.analytics_agents.opo_monitoring_service.services as services


def test_get_trend_series_reads_from_file(tmp_path, monkeypatch):
    dataset = {
        "trend_table": "postgres.overlay_kpi_trend",
        "series": [
            {"machine": "NXE900", "product": "ProductZ", "baseline": 87.5, "degradation_pct": 10.0, "dip_days": 2}
        ],
    }
    data_file = tmp_path / "opo_data.json"
    data_file.write_text(json.dumps(dataset), encoding="utf-8")
    monkeypatch.setattr(query_engine_client, "DATA_FILE", data_file)
    monkeypatch.setattr(query_engine_client, "_dataset_cache", None)

    rows = services.get_trend_series(days=3)

    assert rows[0]["machine"] == "NXE900"
    assert rows[0]["product"] == "ProductZ"
    assert len(rows[0]["points"]) == 3
    assert "trend_table" in services.get_dataset_metadata()


def test_query_wafer_data_uses_file_rows(tmp_path, monkeypatch):
    dataset = {
        "wafer_table": "starrocks.overlay_wafer_points",
        "wafer_rows": [
            {"wafer_id": "W010", "machine": "NXE900", "overlay_um": 0.12, "alignment_um": 0.08, "epe_um": 0.07, "defect_density": 0.2},
            {"wafer_id": "W011", "machine": "NXE900", "overlay_um": 0.34, "alignment_um": 0.22, "epe_um": 0.15, "defect_density": 1.1},
        ],
    }
    data_file = tmp_path / "opo_data.json"
    data_file.write_text(json.dumps(dataset), encoding="utf-8")
    monkeypatch.setattr(query_engine_client, "DATA_FILE", data_file)
    monkeypatch.setattr(query_engine_client, "_dataset_cache", None)

    result = services.query_wafer_data("WS-123", "starrocks.overlay_wafer_points")

    assert result["table"] == "starrocks.overlay_wafer_points"
    assert result["anomalous_wafers"] == ["W011"]
    assert result["rows"][0]["wafer_id"] == "W010"


def test_capability_registry_records_audited_invocation(tmp_path):
    session_memory.configure_store(tmp_path / "events.sqlite")
    token = session_memory.set_session_id("session-test")
    try:
        invoke("workspace.create", permissions={"workspace:create"})
        events = session_memory.get_store().list_events("session-test")
    finally:
        session_memory.reset_session_id(token)

    assert "workspace.create" in [item["name"] for item in list_capabilities()]
    assert [event["event_type"] for event in events] == ["tool_invocation", "tool_result"]
    assert events[-1]["duration_ms"] is not None


def test_capability_registry_rejects_missing_permission():
    try:
        invoke("query_engine.read_trends", permissions=set(), table=None)
    except PermissionError as error:
        assert "query:trends:read" in str(error)
    else:
        raise AssertionError("Expected missing capability permission to be rejected")
