"""Application BFF: HTTP endpoints, display routes, agent invocation (v2).

Ported from the original demonstrator's ``api.py``. Serves the same static UI
assets in place (read-only reference to ``ApplicationUI/opo_monitoring_ui/static``)
so the UI is not duplicated or forked; only the backend wiring changes to match
the target architecture (MCP-backed services, PostgreSQL-backed sessions and
checkpoints, PydanticAI application agents).
"""

import logging
import threading
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command
from plotly.offline import get_plotlyjs
from pydantic import BaseModel

from agent_runtime.graph import build_graph
from application_ui.opo_monitoring_service import services
from foundation import session_manager
from foundation.config import get_settings as get_foundation_settings
from foundation.model_gateway import get_model
from mcp_capability_adaptor.server_analytics_api import mcp as analytics_api_mcp

log = logging.getLogger(__name__)

# Read-only reference to the original demonstrator's static assets - not copied,
# not modified, so there is a single source of truth for the UI (see PLAN.md).
STATIC_DIR = Path(__file__).parents[3] / "ApplicationUI" / "opo_monitoring_ui" / "static"

app = FastAPI(title="OPO Monitoring Service (v2 - target architecture)")
session_manager.configure_store(get_foundation_settings().database_url)


@app.on_event("startup")
def _warm_caches() -> None:
    """Pay the one-time mock dataset load cost now, not on the first user request.

    The model-credential fetch is warmed in a background thread instead of
    inline: DefaultAzureCredential's IMDS/managed-identity probe can hang for
    minutes with no reachable Azure endpoint (e.g. this service's own
    in-cluster deployment before a managed/workload identity is configured -
    see PLAN.md Phase 6 open decisions), and blocking ASGI startup on it would
    make the whole service - including the agent-free `/trends` route - fail
    to become ready.
    """
    threading.Thread(target=_warm_model_client, name="warm-model-client", daemon=True).start()
    try:
        services.get_display_trend_series()
    except Exception:
        log.warning("Could not pre-warm mock datasets", exc_info=True)


def _warm_model_client() -> None:
    try:
        get_model()
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
        "start_date": result.get("start_date"),
        "end_date": result.get("end_date"),
        "lot_ids": result.get("lot_ids"),
        "product_ids": result.get("product_ids"),
        "layer_ids": result.get("layer_ids"),
        "exposure_equipment_ids": result.get("exposure_equipment_ids"),
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
        "selected_action": result.get("selected_action"),
        "spatial_pattern": result.get("spatial_pattern"),
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
    session_manager.record_event(
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
        session_manager.record_event(
            "final_finding",
            {"findings": response["findings"]},
            session_id=thread_id,
            source="application",
        )


def _invoke(thread_id: str, input_value: Any) -> dict:
    token = session_manager.set_session_id(thread_id)
    started = time.perf_counter()
    try:
        result = _graph().invoke(input_value, {"configurable": {"thread_id": thread_id}})
        response = _shape(result, thread_id)
        _record_response(result, thread_id, response)
        return response
    except Exception as exc:
        session_manager.record_event(
            "workflow_error",
            {"error": str(exc)},
            session_id=thread_id,
            source="application",
        )
        raise
    finally:
        session_manager.record_event(
            "workflow_timing",
            {"status": "completed"},
            session_id=thread_id,
            duration_ms=(time.perf_counter() - started) * 1000,
            source="application",
        )
        session_manager.reset_session_id(token)


@app.post("/chat")
def chat(request: ChatRequest) -> dict:
    thread_id = request.thread_id or str(uuid.uuid4())
    token = session_manager.set_session_id(thread_id)
    try:
        session_manager.record_event(
            "user_request",
            {"message": request.message, "use_tool_calling": request.use_tool_calling},
            session_id=thread_id,
            source="application",
        )
    finally:
        session_manager.reset_session_id(token)
    return _invoke(thread_id, {"question": request.message, "use_tool_calling": request.use_tool_calling})


@app.post("/resume")
def resume(request: ResumeRequest) -> dict:
    token = session_manager.set_session_id(request.thread_id)
    try:
        session_manager.record_event(
            "human_decision",
            {"decision": request.decision},
            session_id=request.thread_id,
            source="application",
        )
    finally:
        session_manager.reset_session_id(token)
    return _invoke(request.thread_id, Command(resume=request.decision))


@app.get("/sessions/{session_id}/events")
def session_events(session_id: str) -> dict:
    """Return structured session events for evidence, audit, and timing review."""
    return {"session_id": session_id, "events": session_manager.get_store().list_events(session_id)}


@app.get("/capabilities")
async def capabilities() -> dict:
    """Expose the governed MCP tools available to this application service."""
    tools = await analytics_api_mcp.list_tools()
    return {"capabilities": [{"name": tool.name, "description": tool.description} for tool in tools]}


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
    """Raw KPI series for the chart. No LLM or agent involved, so the plot renders
    on page load. Calls Foundation directly (no MCP), matching the target diagram's
    `bff ..> query_api : GET /trends, no agent or MCP` display path."""
    return {"series": services.get_display_trend_series()}


class AddFiltersRequest(BaseModel):
    filters: dict[str, Any]


class RegisterRequest(BaseModel):
    dataset: str
    table: str


class QueryWafersRequest(BaseModel):
    table: str
    filters: dict[str, Any] | None = None


# --- Direct (non-conversational) workspace/registration/wafer routes ---------
#
# These back the Java facade's WorkspaceService / RegistrationService /
# WaferDataService interfaces (.github/copilot-instructions.md `## 8`) for the
# traditional (non-agentic) view. They still go through `services.py`, which is
# MCP-backed - Java never reaches Foundation APIs itself, only this API
# (`### 3.5 Shared contracts`, `contracts/workflow-runtime-api/openapi.yaml`).

@app.post("/workspaces")
def create_workspace() -> dict:
    return {"workspace_id": services.create_workspace()}


@app.post("/workspaces/{workspace_id}/filters")
def add_filters(workspace_id: str, request: AddFiltersRequest) -> dict:
    return services.add_filters(workspace_id, request.filters)


@app.post("/workspaces/{workspace_id}/register")
def register_dataset(workspace_id: str, request: RegisterRequest) -> dict:
    return services.register(workspace_id, request.dataset, request.table, approved=True)


@app.post("/workspaces/{workspace_id}/wafers/query")
def query_wafers(workspace_id: str, request: QueryWafersRequest) -> dict:
    return services.query_wafer_data(workspace_id, request.table, request.filters)


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
