import uuid
from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from langgraph.types import Command
from pydantic import BaseModel

from analytics_agent.graph import build_graph

app = FastAPI(title="Analytics Investigation Agent")


@lru_cache
def _graph():
    return build_graph()


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ResumeRequest(BaseModel):
    thread_id: str
    decision: Any = True


def _shape(result: dict, thread_id: str) -> dict:
    interrupts = result.get("__interrupt__")
    if interrupts:
        return {
            "thread_id": thread_id,
            "status": "awaiting_human",
            "request": interrupts[0].value,
        }

    return {
        "thread_id": thread_id,
        "status": "complete",
        "findings": result.get("findings"),
        # Evidence comes from graph state, not from model prose, so it cannot be fabricated
        "evidence": {
            "selected_outlier": result.get("selected"),
            "workspace_id": result.get("workspace_id"),
            "filters": result.get("filters"),
            "registration": result.get("registration"),
            "registration_history": result.get("registration_history"),
            "anomalous_wafers": (result.get("wafer_data") or {}).get("anomalous_wafers"),
        },
    }


@app.post("/chat")
def chat(request: ChatRequest) -> dict:
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    result = _graph().invoke({"question": request.message}, config)
    return _shape(result, thread_id)


@app.post("/resume")
def resume(request: ResumeRequest) -> dict:
    config = {"configurable": {"thread_id": request.thread_id}}
    result = _graph().invoke(Command(resume=request.decision), config)
    return _shape(result, request.thread_id)
