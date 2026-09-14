"""OPO monitoring service, the application-owned BFF and agent backend.

Application-specific: KPI/outlier semantics, the LangGraph investigation workflow,
and the FastAPI API that exposes it. The frontend is in ``ApplicationUI/opo_monitoring_ui``.
The service connects to Analytics Foundation (model gateway, Workspace API, Query
Engine) via the ``AnalyticsFoundation`` package.
"""
