"""StarRocks MCP server: governed read-only tools over wafer-level analytical data.

Maps to the target diagram's ``mcp -> query_api`` path for point-level (StarRocks)
reads. Backed by ``foundation/clients/datawarehouse.py`` (mocked JDBC today).
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from foundation.clients import datawarehouse

mcp = FastMCP("analytics-foundation-starrocks")


@mcp.tool()
def get_wafer_table_metadata() -> dict[str, Any]:
    """Logical table/column mapping for the wafer-level StarRocks table."""
    return datawarehouse.get_table_metadata()


@mcp.tool()
def read_wafers(
    table: str | None = None,
    connection_info: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Raw wafer rows for the given table/connection. No filtering or business logic."""
    return datawarehouse.query_wafer_rows(table=table, connection_info=connection_info)


if __name__ == "__main__":
    mcp.run()
