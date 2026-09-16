#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE=".v2-monitoring.pid"
LOG_FILE=".v2-monitoring.log"
COMMAND="${1:-start}"

find_python() {
  if [[ -x ".venv/Scripts/python.exe" ]]; then
    PYTHON=".venv/Scripts/python.exe"
  elif [[ -x ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
  else
    printf '%s\n' "Python 3 was not found. Install Python 3.12 or newer and rerun run.sh." >&2
    exit 1
  fi
}

service_running() {
  [[ -f "$PID_FILE" ]] || return 1
  local pid
  pid="$(<"$PID_FILE")"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

start_service() {
  if service_running; then
    printf '%s\n' "v2 OPO Monitoring Service is already running (PID $(<"$PID_FILE"))."
    exit 0
  fi

  find_python
  if [[ ! -x ".venv/Scripts/python.exe" && ! -x ".venv/bin/python" ]]; then
    printf '%s\n' "Creating virtual environment in .venv..."
    "$PYTHON" -m venv .venv
    if [[ -x ".venv/Scripts/python.exe" ]]; then
      PYTHON=".venv/Scripts/python.exe"
    else
      PYTHON=".venv/bin/python"
    fi
  fi

  printf '%s\n' "Installing Python dependencies..."
  "$PYTHON" -m pip install --upgrade pip
  "$PYTHON" -m pip install -r requirements.txt

  printf '%s\n' "Reminder: start PostgreSQL first, e.g. 'docker compose up -d'."

  PORT="${ASML_AI_V2_PORT:-8100}"
  HOST="${ASML_AI_V2_HOST:-127.0.0.1}"
  URL="http://${HOST}:${PORT}/"
  printf '%s\n' "Starting v2 OPO Monitoring Service and UI at ${URL}"
  PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}" "$PYTHON" -m uvicorn application_ui.opo_monitoring_service.api:app \
    --host "$HOST" \
    --port "$PORT" > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  printf '%s\n' "Started with PID $(<"$PID_FILE"). Logs: $LOG_FILE"
}

stop_service() {
  if ! service_running; then
    rm -f "$PID_FILE"
    printf '%s\n' "v2 OPO Monitoring Service is not running."
    return 0
  fi

  local pid
  pid="$(<"$PID_FILE")"
  kill "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  printf '%s\n' "Stopped v2 OPO Monitoring Service (PID $pid)."
}

status_service() {
  if service_running; then
    printf '%s\n' "v2 OPO Monitoring Service is running (PID $(<"$PID_FILE"))."
  else
    printf '%s\n' "v2 OPO Monitoring Service is stopped."
    exit 1
  fi
}

case "$COMMAND" in
  start)
    start_service
    ;;
  stop)
    stop_service
    ;;
  restart)
    stop_service
    start_service
    ;;
  status)
    status_service
    ;;
  *)
    printf '%s\n' "Usage: $0 {start|stop|restart|status}" >&2
    exit 1
    ;;
esac
