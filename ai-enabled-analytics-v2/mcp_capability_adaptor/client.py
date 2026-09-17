"""In-process MCP client used by ``application_ui`` and ``agent_runtime``.

Calls tools directly against the FastMCP server objects in-process (default dev
transport per ``foundation.config.mcp_transport == "stdio"``-equivalent single
process loop). This is the one path from workflow/service code to Foundation
APIs — no module here imports ``foundation.clients`` directly; everything goes
through these tool calls, matching the target diagram's MCP boundary.
"""

from __future__ import annotations

import asyncio
from typing import Any

from mcp_capability_adaptor import server_analytics_api, server_starrocks


def _call_tool_sync(mcp_server, tool_name: str, arguments: dict[str, Any]) -> Any:
    async def _call() -> Any:
        result = await mcp_server.call_tool(tool_name, arguments)
        # FastMCP wraps tool results in content blocks plus a structured payload;
        # prefer the structured value so callers get plain Python data back.
        if isinstance(result, tuple) and len(result) == 2:
            _content, structured = result
            if isinstance(structured, dict) and "result" in structured:
                return structured["result"]
            return structured
        return result

    return asyncio.run(_call())


# --- StarRocks --------------------------------------------------------------

def get_wafer_table_metadata() -> dict[str, Any]:
    return _call_tool_sync(server_starrocks.mcp, "get_wafer_table_metadata", {})


def read_wafers(table: str | None = None, connection_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return _call_tool_sync(
        server_starrocks.mcp, "read_wafers", {"table": table, "connection_info": connection_info}
    )


# --- Analytics API (Workspace / Query Engine / Processing / Assets / LandaDB) --

def create_workspace() -> str:
    return _call_tool_sync(server_analytics_api.mcp, "create_workspace", {})


def add_workspace_filters(workspace_id: str, filters: dict[str, Any]) -> dict[str, Any]:
    return _call_tool_sync(
        server_analytics_api.mcp, "add_workspace_filters", {"workspace_id": workspace_id, "filters": filters}
    )


def register_dataset(workspace_id: str, dataset: str, table: str) -> dict[str, Any]:
    return _call_tool_sync(
        server_analytics_api.mcp,
        "register_dataset",
        {"workspace_id": workspace_id, "dataset": dataset, "table": table},
    )


def get_workspace_connection_info(workspace_id: str) -> dict[str, Any]:
    return _call_tool_sync(
        server_analytics_api.mcp, "get_workspace_connection_info", {"workspace_id": workspace_id}
    )


def get_trend_table_metadata() -> dict[str, Any]:
    return _call_tool_sync(server_analytics_api.mcp, "get_trend_table_metadata", {})


def read_trends(table: str | None = None, connection_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return _call_tool_sync(
        server_analytics_api.mcp, "read_trends", {"table": table, "connection_info": connection_info}
    )


def get_kpi_distribution_stats(
    days: int | None = 14,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
) -> dict[str, Any]:
    return _call_tool_sync(
        server_analytics_api.mcp,
        "get_kpi_distribution_stats",
        {
            "days": days,
            "start_date": start_date,
            "end_date": end_date,
            "lot_ids": lot_ids,
            "product_ids": product_ids,
            "layer_ids": layer_ids,
            "exposure_equipment_ids": exposure_equipment_ids,
        },
    )
