"""Hive MCP server (boundary placeholder, not wired into the OPO workflow).

Hive is internal to Analytics Foundation and is not exposed as an MCP tool per
the target architecture note ("Hive and Kafka are internal, therefore not exposed
as MCP tools"). This stub exists so the component boundary is visible in the repo
layout ahead of any real integration; it registers no tools yet.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("analytics-foundation-hive-stub")


if __name__ == "__main__":
    mcp.run()
