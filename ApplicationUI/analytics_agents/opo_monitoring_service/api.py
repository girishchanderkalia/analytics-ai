import uuid
import time
import logging
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command
from plotly.offline import get_plotlyjs
from pydantic import BaseModel

from AnalyticsFoundation import datawarehouse, lanadb_query, session_memory
from AnalyticsFoundation.capability_registry import list_capabilities
from AnalyticsFoundation.config import get_settings as get_platform_settings
from AnalyticsFoundation.model_gateway import get_llm
from ApplicationUI.analytics_agents.opo_monitoring_service import services
from ApplicationUI.analytics_agents.opo_monitoring_service.application_workflow import build_graph

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parents[2] / "opo_monitoring_ui" / "static"

app = FastAPI(title="OPO Monitoring Service")
session_memory.configure_store(get_platform_settings().session_db)


@app.on_event("startup")
def _warm_caches() -> None:
    """Pay the one-time model-credential fetch and mock dataset load costs now,
    not on the first user request (Key Vault auth alone can take several seconds,
    and unpacking the wafer dataset the first time takes a couple more)."""
    threading.Thread(target=_warm_model_client, name="model-warmup", daemon=True).start()
    try:
        lanadb_query.query_trend_rows()
        datawarehouse.query_wafer_rows()
    except Exception:
        log.warning("Could not pre-warm mock datasets", exc_info=True)


def _warm_model_client() -> None:
    try:
        get_llm()
    except Exception:
        log.warning("Could not pre-warm the model client", exc_info=True)


@app.middleware("http")
async def no_cache_app_assets(request, call_next):
    """Stop browsers serving a stale index.html or app.js after an edit."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
    return response


@lru_cache
def _graph():
    return build_graph()


@lru_cache
def _plotly_bundle() -> str:
    return get_plotlyjs()


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
    use_tool_calling: bool = False


class ResumeRequest(BaseModel):
    thread_id: str
    decision: Any = True


def _evidence(result: dict) -> dict:
    # Read from graph state, not model prose, so it cannot be fabricated
    return {
        "mode": result.get("mode"),
        "limit_value": result.get("limit_value"),
        "requested_limit_value": result.get("requested_limit_value"),
        "direction": result.get("direction"),
        "threshold_unit": result.get("threshold_unit"),
        "baseline_deviation_pct": result.get("baseline_deviation_pct"),
        "threshold_context": result.get("threshold_context"),
        "threshold_recommendation": result.get("threshold_recommendation"),
        "interpretation": result.get("interpretation"),
        "lookback_days": result.get("lookback_days"),
        "machine_id": result.get("machine_id"),
        "lot_id": result.get("lot_id"),
        "product_id": result.get("product_id"),
        "layer_id": result.get("layer_id"),
        "exposure_equipment_id": result.get("exposure_equipment_id"),
        "trend_series": result.get("trend_series"),
        "analysis": result.get("analysis"),
        "outliers": result.get("outliers"),
        "selected_outlier": result.get("selected"),
        "workspace_id": result.get("workspace_id"),
        "filters": result.get("filters"),
        "registration": result.get("registration"),
        "registration_history": result.get("registration_history"),
        "anomalous_wafers": (result.get("wafer_data") or {}).get("anomalous_wafers"),
        "wafer_rows": (result.get("wafer_data") or {}).get("rows"),
    }


def _shape(result: dict, thread_id: str) -> dict:
    evidence = _evidence(result)
    interrupts = result.get("__interrupt__")

    if interrupts:
        return {
            "thread_id": thread_id,
            "status": "awaiting_human",
            "request": interrupts[0].value,
            "evidence": evidence,
        }

    if result.get("cancelled_at"):
        return {
            "thread_id": thread_id,
            "status": "cancelled",
            "cancelled_at": result["cancelled_at"],
            "evidence": evidence,
        }

    if not result.get("outliers"):
        return {
            "thread_id": thread_id,
            "status": "no_outliers",
            "evidence": evidence,
        }

    return {
        "thread_id": thread_id,
        "status": "complete",
        "findings": result.get("findings"),
        "evidence": evidence,
    }


def _record_response(result: dict, thread_id: str, response: dict) -> None:
    evidence = _evidence(result)
    session_memory.record_event(
        "evidence_item",
        {
            "status": response.get("status"),
            "mode": evidence.get("mode"),
            "outlier_count": len(evidence.get("outliers") or []),
            "selected_outlier": evidence.get("selected_outlier"),
            "workspace_id": evidence.get("workspace_id"),
            "registration": evidence.get("registration"),
            "anomalous_wafers": evidence.get("anomalous_wafers"),
        },
        session_id=thread_id,
        source="application",
    )
    if response.get("findings"):
        session_memory.record_event(
            "final_finding",
            {"findings": response["findings"]},
            session_id=thread_id,
            source="application",
        )


def _invoke(thread_id: str, input_value: Any) -> dict:
    token = session_memory.set_session_id(thread_id)
    started = time.perf_counter()
    try:
        result = _graph().invoke(input_value, {"configurable": {"thread_id": thread_id}})
        response = _shape(result, thread_id)
        _record_response(result, thread_id, response)
        return response
    except Exception as exc:
        session_memory.record_event(
            "workflow_error",
            {"error": str(exc)},
            session_id=thread_id,
            source="application",
        )
        raise
    finally:
        session_memory.record_event(
            "workflow_timing",
            {"status": "completed"},
            session_id=thread_id,
            duration_ms=(time.perf_counter() - started) * 1000,
            source="application",
        )
        session_memory.reset_session_id(token)


@app.post("/chat")
def chat(request: ChatRequest) -> dict:
    thread_id = request.thread_id or str(uuid.uuid4())
    token = session_memory.set_session_id(thread_id)
    try:
        session_memory.record_event(
            "user_request",
            {"message": request.message, "use_tool_calling": request.use_tool_calling},
            session_id=thread_id,
            source="application",
        )
    finally:
        session_memory.reset_session_id(token)
    return _invoke(
        thread_id,
        {"question": request.message, "use_tool_calling": request.use_tool_calling},
    )


@app.post("/resume")
def resume(request: ResumeRequest) -> dict:
    token = session_memory.set_session_id(request.thread_id)
    try:
        session_memory.record_event(
            "human_decision",
            {"decision": request.decision},
            session_id=request.thread_id,
            source="application",
        )
    finally:
        session_memory.reset_session_id(token)
    return _invoke(request.thread_id, Command(resume=request.decision))


@app.get("/sessions/{session_id}/events")
def session_events(session_id: str) -> dict:
    """Return structured session events for evidence, audit, and timing review."""
    return {"session_id": session_id, "events": session_memory.get_store().list_events(session_id)}


@app.get("/capabilities")
def capabilities() -> dict:
    """Expose the platform capabilities available to this application service."""
    return {"capabilities": list_capabilities()}


@app.get("/threads/{thread_id}")
def thread_state(thread_id: str) -> dict:
    """Reopen a parked investigation, including one paused before a restart."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = _graph().get_state(config)
    pending = [i.value for task in snapshot.tasks for i in task.interrupts]
    return {
        "thread_id": thread_id,
        "status": "awaiting_human" if pending else "idle",
        "request": pending[0] if pending else None,
        "values": snapshot.values,
    }


@app.get("/trends")
def trends() -> dict:
    """Raw KPI series for the chart. No LLM involved, so the plot renders on page load."""
    return {"series": services.get_trend_series()}


@app.get("/vendor/plotly.js")
def plotly_js() -> Response:
    """Serve the bundle shipped with the plotly package so no CDN is needed."""
    return Response(
        _plotly_bundle(),
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
