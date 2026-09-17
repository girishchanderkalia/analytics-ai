"""Analytics API MCP server: governed tools over Workspace, Query Engine, Processing,
and Assets APIs plus the PostgreSQL (LandaDB) trend table.

Maps to the target diagram's ``mcp -> assets_api / workspace_api / query_api /
processing_api`` paths. Backed by ``foundation/clients/*.py`` (mocked today; a real
deployment swaps the client implementations for HTTPS calls against ``apis/api.yml``
and ``apis/qe_api.yml`` without changing this tool surface).
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from foundation.clients import (
    assets_client,
    lanadb_query,
    processing_client,
    query_engine_client,
    workspace_client,
)

mcp = FastMCP("analytics-foundation-analytics-api")


# --- Workspace API -----------------------------------------------------------

@mcp.tool()
def create_workspace() -> str:
    """Create a new workspace and return its ID."""
    return workspace_client.create_workspace()


@mcp.tool()
def add_workspace_filters(workspace_id: str, filters: dict[str, Any]) -> dict[str, Any]:
    """Apply filters to a workspace."""
    return workspace_client.add_filters(workspace_id, filters)


@mcp.tool()
def register_dataset(workspace_id: str, dataset: str, table: str) -> dict[str, Any]:
    """Register a dataset/table for querying in the workspace (asynchronous upstream)."""
    return workspace_client.register(workspace_id, dataset, table)


@mcp.tool()
def get_workspace_connection_info(workspace_id: str) -> dict[str, Any]:
    """JDBC connection info for the workspace's provisioned database."""
    return workspace_client.get_connection_info(workspace_id)


# --- Query Engine Database API ----------------------------------------------

@mcp.tool()
def database_exists(database_name: str) -> bool:
    return query_engine_client.database_exists(database_name)


@mcp.tool()
def create_database(database_name: str, username: str | None = None, password: str | None = None) -> None:
    query_engine_client.create_database(database_name, username, password)


@mcp.tool()
def get_table_names(database_name: str) -> list[str]:
    return query_engine_client.get_table_names(database_name)


@mcp.tool()
def create_tables(database_name: str, tables: list[dict[str, Any]]) -> None:
    query_engine_client.create_tables(database_name, tables)


# --- Processing API ----------------------------------------------------------

@mcp.tool()
def list_processing_instances(
    workspace_id: str,
    service_name: str | None = None,
    service_version: str | None = None,
) -> list[dict[str, Any]]:
    return processing_client.list_processing_instances(workspace_id, service_name, service_version)


@mcp.tool()
def create_processing_instance(
    workspace_id: str,
    service_name: str,
    service_version: str,
    display_name: str | None = None,
) -> dict[str, Any]:
    return processing_client.create_processing_instance(workspace_id, service_name, service_version, display_name)


@mcp.tool()
def get_processing_instance(workspace_id: str, instance_id: str) -> dict[str, Any]:
    return processing_client.get_processing_instance(workspace_id, instance_id)


@mcp.tool()
def stop_processing_instance(workspace_id: str, instance_id: str) -> dict[str, Any]:
    return processing_client.stop_processing_instance(workspace_id, instance_id)


# --- Assets API ---------------------------------------------------------------

@mcp.tool()
def list_assets(type: str | None = None, name: str | None = None, sharing: str | None = None) -> list[dict[str, Any]]:
    return assets_client.list_assets(type, name, sharing)


@mcp.tool()
def get_asset(asset_id: str) -> dict[str, Any]:
    return assets_client.get_asset(asset_id)


@mcp.tool()
def add_asset(
    name: str,
    type: str,
    description: str | None = None,
    sharing: str = "private",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return assets_client.add_asset(name, type, description, sharing, metadata)


# --- PostgreSQL (LandaDB) trend reads -----------------------------------------

@mcp.tool()
def get_trend_table_metadata() -> dict[str, Any]:
    """Logical table/column mapping for the high-level KPI/trend PostgreSQL table."""
    return lanadb_query.get_table_metadata()


@mcp.tool()
def read_trends(table: str | None = None, connection_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Raw trend rows for the given table/connection. No filtering or business logic."""
    return lanadb_query.query_trend_rows(table=table, connection_info=connection_info)


@mcp.tool()
def get_kpi_distribution_stats(
    days: int | None = 14,
    start_date: str | None = None,
    end_date: str | None = None,
    lot_ids: list[str] | None = None,
    product_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    exposure_equipment_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Sample count, min/max, mean, stdev, p95/p99 and a bell-curve spread band for the
    (optionally filtered) trend table, computed here so only the summary - not the raw
    rows - crosses this tool boundary."""
    return lanadb_query.compute_kpi_distribution_stats(
        days=days,
        start_date=start_date,
        end_date=end_date,
        lot_ids=lot_ids,
        product_ids=product_ids,
        layer_ids=layer_ids,
        exposure_equipment_ids=exposure_equipment_ids,
    )


if __name__ == "__main__":
    mcp.run()
