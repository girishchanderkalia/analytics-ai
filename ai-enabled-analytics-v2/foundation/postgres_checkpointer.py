"""PostgreSQL-backed LangGraph checkpointer (Phase 2 of PLAN.md).

Replaces the original demonstrator's ``langgraph.checkpoint.sqlite.SqliteSaver``
with ``langgraph.checkpoint.postgres.PostgresSaver`` so graph resumes survive
process restarts against the single PostgreSQL runtime-state store described in
``agentWorkflows/mcp-oss-target-architecture.puml``.
"""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from foundation.config import get_settings


def build_checkpointer() -> PostgresSaver:
    """Build a PostgresSaver backed by a connection pool, creating its tables.

    A pool (not a single bare connection from ``PostgresSaver.from_conn_string``)
    is required here: this checkpointer is reused for the whole process
    lifetime, and a lone psycopg connection does not reconnect once the
    network drops it - observed in practice in-cluster as
    ``psycopg.OperationalError: the connection is closed`` on every request
    after the first idle period. The pool transparently opens a fresh
    connection per operation instead.
    """
    settings = get_settings()
    pool = ConnectionPool(
        conninfo=settings.database_url,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    return checkpointer
