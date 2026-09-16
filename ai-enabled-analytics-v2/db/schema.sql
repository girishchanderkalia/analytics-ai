-- PostgreSQL runtime state schema for ai-enabled-analytics-v2 (PLAN.md Phase 2).
--
-- LangGraph checkpoint tables are created separately by
-- `langgraph.checkpoint.postgres.PostgresSaver.setup()` (see
-- foundation/postgres_checkpointer.py) and are NOT part of this file, per the
-- target architecture's separation of "checkpoints resume execution" from
-- "Session Manager records the evidence and audit trail" (same PostgreSQL
-- runtime-state store, separate table groups).

CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_session_events (
    event_id     TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL REFERENCES sessions(session_id),
    event_type   TEXT NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL,
    duration_ms  DOUBLE PRECISION,
    source       TEXT NOT NULL,
    payload_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_session_events_session
    ON agent_session_events (session_id, timestamp);

CREATE TABLE IF NOT EXISTS workspace_registrations (
    workspace_id TEXT PRIMARY KEY,
    session_id   TEXT REFERENCES sessions(session_id),
    dataset      TEXT NOT NULL,
    table_name   TEXT NOT NULL,
    status       TEXT NOT NULL,
    progress_pct INTEGER,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memory (
    memory_key   TEXT PRIMARY KEY,
    session_id   TEXT REFERENCES sessions(session_id),
    value_json   JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
