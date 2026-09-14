"""Analytics Foundation platform package.

Provides the platform capabilities that any application agent (built with
LangGraph or another framework) integrates with:

- ``config`` / ``model_gateway``: connection to the LLM.
- ``workspace_client``: Workspace API (create workspace, apply filters, register datasets).
- ``query_engine_client``: Query Engine API over PostgreSQL (trend/KPI tables) and
  StarRocks (wafer-level tables).

Application-specific logic (KPI semantics, outlier rules, workflow graphs, UI) does
not live here - see ``ApplicationUI``.
"""
