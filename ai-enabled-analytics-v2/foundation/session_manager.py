"""Platform-owned session events and evidence records, backed by PostgreSQL.

Same public surface as the original demonstrator's ``AnalyticsFoundation/session_memory.py``
(``configure_store``, ``record_event``, ``timed_event``, ``set_session_id``,
``current_session_id``, ``get_store().list_events``) so callers do not need to
change shape, but the storage engine is now the shared PostgreSQL runtime-state
store instead of a per-project SQLite file (Phase 2 of PLAN.md). LangGraph
checkpoints remain a separate table group managed by ``postgres_checkpointer.py``.
"""

from __future__ import annotations

import contextvars
import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

_current_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "foundation_session_id", default=None
)


def set_session_id(session_id: str):
    return _current_session_id.set(session_id)


def reset_session_id(token: contextvars.Token):
    _current_session_id.reset(token)


def current_session_id() -> str | None:
    return _current_session_id.get()


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return str(value)


class SessionEventStore:
    """PostgreSQL-backed event store for session, evidence, and timing records."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def ensure_session(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (session_id, created_at)
                VALUES (%s, %s)
                ON CONFLICT (session_id) DO NOTHING
                """,
                (session_id, datetime.now(timezone.utc)),
            )

    def append(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        session_id: str | None = None,
        duration_ms: float | None = None,
        source: str = "platform",
    ) -> str | None:
        resolved_session_id = session_id or current_session_id()
        if not resolved_session_id:
            return None

        self.ensure_session(resolved_session_id)
        event_id = f"EV-{uuid.uuid4().hex[:12].upper()}"
        timestamp = datetime.now(timezone.utc)
        serialized_payload = json.dumps(_json_value(payload or {}))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_session_events
                (event_id, session_id, event_type, timestamp, duration_ms, source, payload_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    resolved_session_id,
                    event_type,
                    timestamp,
                    duration_ms,
                    source,
                    serialized_payload,
                ),
            )
        return event_id

    def list_events(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, session_id, event_type, timestamp, duration_ms, source, payload_json
                FROM agent_session_events
                WHERE session_id = %s
                ORDER BY timestamp, event_id
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "session_id": row["session_id"],
                "event_type": row["event_type"],
                "timestamp": row["timestamp"].isoformat(),
                "duration_ms": row["duration_ms"],
                "source": row["source"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]


_store: SessionEventStore | None = None


def configure_store(database_url: str) -> SessionEventStore:
    global _store
    _store = SessionEventStore(database_url)
    return _store


def get_store() -> SessionEventStore:
    if _store is None:
        from foundation.config import get_settings

        return configure_store(get_settings().database_url)
    return _store


def record_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    session_id: str | None = None,
    duration_ms: float | None = None,
    source: str = "platform",
) -> str | None:
    return get_store().append(
        event_type, payload, session_id=session_id, duration_ms=duration_ms, source=source
    )


@contextmanager
def timed_event(event_type: str, payload: dict[str, Any] | None = None, *, source: str = "platform") -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        record_event(event_type, payload, duration_ms=(time.perf_counter() - started) * 1000, source=source)
