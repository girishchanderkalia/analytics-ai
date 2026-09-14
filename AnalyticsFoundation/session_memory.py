"""Platform-owned session events and evidence records.

LangGraph checkpoints remain responsible for resumable execution. This store is a
separate, framework-neutral record of what happened during an agent session.
"""

from __future__ import annotations

import contextvars
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_current_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "analytics_foundation_session_id", default=None
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
    """SQLite-backed event store for session, evidence, and timing records."""

    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._setup()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path, check_same_thread=False)

    def _setup(self) -> None:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_session_events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_ms REAL,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_session_events_session
                ON agent_session_events(session_id, timestamp)
                """
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

        event_id = f"EV-{uuid.uuid4().hex[:12].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()
        serialized_payload = json.dumps(_json_value(payload or {}), separators=(",", ":"))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_session_events
                (event_id, session_id, event_type, timestamp, duration_ms, source, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
                WHERE session_id = ?
                ORDER BY timestamp, event_id
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "event_id": row[0],
                "session_id": row[1],
                "event_type": row[2],
                "timestamp": row[3],
                "duration_ms": row[4],
                "source": row[5],
                "payload": json.loads(row[6]),
            }
            for row in rows
        ]


_store: SessionEventStore | None = None


def configure_store(database_path: str | Path) -> SessionEventStore:
    global _store
    _store = SessionEventStore(database_path)
    return _store


def get_store() -> SessionEventStore:
    if _store is None:
        return configure_store("agent_sessions.sqlite")
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
        event_type,
        payload,
        session_id=session_id,
        duration_ms=duration_ms,
        source=source,
    )


def timed_event(event_type: str, payload: dict[str, Any] | None = None, *, source: str = "platform"):
    """Return a small context manager that records elapsed time for an event."""

    class _TimedEvent:
        def __enter__(self):
            self.started = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            duration_ms = (time.perf_counter() - self.started) * 1000
            event_payload = dict(payload or {})
            if exc_value is not None:
                event_payload["error"] = str(exc_value)
            record_event(
                event_type,
                event_payload,
                duration_ms=duration_ms,
                source=source,
            )
            return False

    return _TimedEvent()
