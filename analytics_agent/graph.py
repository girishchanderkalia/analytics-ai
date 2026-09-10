"""Investigation workflow.

The pipeline is deterministic, so each mechanical step is a code node rather than a
tool call the model could skip or fabricate. The LLM is used only to interpret the
findings at the end. Human gates are `interrupt()` points, resumable via checkpointing.
"""

import sqlite3
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from analytics_agent import services
from analytics_agent.config import get_settings
from analytics_agent.llm import get_llm

MAX_REGISTRATION_POLLS = 10


def _keep_last(_current: Any, incoming: Any) -> Any:
    return incoming


class InvestigationState(TypedDict, total=False):
    question: str
    outliers: Annotated[list[dict], _keep_last]
    selected: dict
    workspace_id: str
    filters: dict
    registration: dict
    registration_history: Annotated[list[dict], _keep_last]
    wafer_data: dict
    findings: str


def analyze_trends(state: InvestigationState) -> InvestigationState:
    outliers = sorted(
        services.get_trends(), key=lambda o: o["yield_degradation"], reverse=True
    )
    return {"outliers": outliers}


def confirm_investigation(state: InvestigationState) -> InvestigationState:
    candidate = state["outliers"][0]
    decision = interrupt(
        {
            "type": "confirm_investigation",
            "question": "Investigate the most significant outlier?",
            "candidate": candidate,
            "all_outliers": state["outliers"],
        }
    )
    if isinstance(decision, dict) and "machine" in decision:
        chosen = next(
            (o for o in state["outliers"] if o["machine"] == decision["machine"]),
            candidate,
        )
    else:
        chosen = candidate
    return {"selected": chosen}


def create_workspace(state: InvestigationState) -> InvestigationState:
    return {"workspace_id": services.create_workspace()}


def apply_filters(state: InvestigationState) -> InvestigationState:
    selected = state["selected"]
    filters = {"machine": selected["machine"], "product": selected["product"]}
    services.add_filters(state["workspace_id"], filters)
    return {"filters": filters}


def approve_registration(state: InvestigationState) -> InvestigationState:
    interrupt(
        {
            "type": "approve_registration",
            "question": "Approve dataset registration? This provisions compute upstream.",
            "workspace_id": state["workspace_id"],
            "dataset": "wafer_yield",
            "filters": state["filters"],
        }
    )
    return {}


def register_and_wait(state: InvestigationState) -> InvestigationState:
    workspace_id = state["workspace_id"]
    history: list[dict] = []

    for _ in range(MAX_REGISTRATION_POLLS):
        status = services.register(workspace_id, "wafer_yield", "wafer_yield")
        history.append(status)
        if status["status"] == "READY":
            return {"registration": status, "registration_history": history}

    raise TimeoutError(
        f"Registration for {workspace_id} did not reach READY "
        f"within {MAX_REGISTRATION_POLLS} polls"
    )


def query_wafers(state: InvestigationState) -> InvestigationState:
    return {
        "wafer_data": services.query_wafer_data(
            state["workspace_id"], state["registration"]["table"]
        )
    }


def summarise(state: InvestigationState) -> InvestigationState:
    wafer_data = state["wafer_data"]
    prompt = (
        "You are an Analytics Investigation Agent for semiconductor yield analysis.\n"
        "Summarise these findings concisely: findings, evidence, recommended next actions.\n"
        "Use only the values given below. Do not invent identifiers or time ranges.\n\n"
        f"Outlier: {state['selected']}\n"
        f"Filters applied: {state['filters']}\n"
        f"Workspace: {state['workspace_id']}\n"
        f"Registration: {state['registration']}\n"
        f"Wafer rows: {wafer_data['rows']}\n"
        f"Anomalous wafers: {wafer_data['anomalous_wafers']}\n"
    )
    return {"findings": get_llm().invoke(prompt).content}


def build_graph():
    builder = StateGraph(InvestigationState)

    builder.add_node("analyze_trends", analyze_trends)
    builder.add_node("confirm_investigation", confirm_investigation)
    builder.add_node("create_workspace", create_workspace)
    builder.add_node("apply_filters", apply_filters)
    builder.add_node("approve_registration", approve_registration)
    builder.add_node("register_and_wait", register_and_wait)
    builder.add_node("query_wafers", query_wafers)
    builder.add_node("summarise", summarise)

    builder.add_edge(START, "analyze_trends")
    builder.add_edge("analyze_trends", "confirm_investigation")
    builder.add_edge("confirm_investigation", "create_workspace")
    builder.add_edge("create_workspace", "apply_filters")
    builder.add_edge("apply_filters", "approve_registration")
    builder.add_edge("approve_registration", "register_and_wait")
    builder.add_edge("register_and_wait", "query_wafers")
    builder.add_edge("query_wafers", "summarise")
    builder.add_edge("summarise", END)

    # check_same_thread=False so the graph is usable from FastAPI's worker threads
    conn = sqlite3.connect(get_settings().checkpoint_db, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    return builder.compile(checkpointer=checkpointer)
