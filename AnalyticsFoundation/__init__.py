"""Analytics Foundation platform package.

Provides the platform capabilities that any application agent (built with
LangGraph or another framework) integrates with:

- ``config`` / ``model_gateway``: connection to the LLM.
- ``workspace_client``: Workspace API (create workspace, apply filters, register datasets).
- ``query_engine_client``: Query Engine API (create/inspect databases and tables).
- ``lanadb_query``: PostgreSQL API (KPI/trend row reads).
- ``datawarehouse``: StarRocks API (wafer-level row reads).
- ``assets_client``: Assets API (available assets and platform metadata).
- ``processing_client``: Processing API (processing instance lifecycle).

Application-specific logic (KPI semantics, outlier rules, workflow graphs, UI) does
not live here - see ``ApplicationUI``.
"""
