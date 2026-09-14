#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE=".opo-monitoring.pid"
LOG_FILE=".opo-monitoring.log"
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

read_port() {
  PORT="${ASML_AI_PORT:-8000}"
  if [[ -f .opo-monitoring.port ]]; then
    PORT="$(<.opo-monitoring.port)"
  fi
}

start_service() {
  if service_running; then
    read_port
    printf '%s\n' "OPO Monitoring Service is already running (PID $(<"$PID_FILE")) at http://127.0.0.1:${PORT}/"
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

  PORT="${ASML_AI_PORT:-8000}"
  if command -v powershell.exe >/dev/null 2>&1; then
    if ! powershell.exe -NoProfile -Command "if (Get-NetTCPConnection -LocalPort $PORT -State Listen -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >/dev/null 2>&1; then
      PORT="${ASML_AI_FALLBACK_PORT:-8010}"
    fi
  elif "$PYTHON" -c "import socket; s=socket.socket(); s.settimeout(0.2); code=s.connect_ex(('127.0.0.1', int('$PORT'))); s.close(); raise SystemExit(code == 0)"; then
    PORT="${ASML_AI_FALLBACK_PORT:-8010}"
  fi

  printf '%s\n' "$PORT" > .opo-monitoring.port
  URL="http://127.0.0.1:${PORT}/"
  printf '%s\n' "Starting OPO Monitoring Service and UI at ${URL}"
  "$PYTHON" -m uvicorn ApplicationUI.analytics_agents.opo_monitoring_service.api:app \
    --host "${ASML_AI_HOST:-127.0.0.1}" \
    --port "$PORT" > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  printf '%s\n' "Started with PID $(<"$PID_FILE"). Logs: $LOG_FILE"
}

stop_service() {
  if ! service_running; then
    rm -f "$PID_FILE" "$PWD/.opo-monitoring.port"
    printf '%s\n' "OPO Monitoring Service is not running."
    return 0
  fi

  local pid
  pid="$(<"$PID_FILE")"
  kill "$pid" 2>/dev/null || true
  rm -f "$PID_FILE" "$PWD/.opo-monitoring.port"
  printf '%s\n' "Stopped OPO Monitoring Service (PID $pid)."
}

status_service() {
  read_port
  if service_running; then
    printf '%s\n' "OPO Monitoring Service is running (PID $(<"$PID_FILE")) at http://127.0.0.1:${PORT}/"
  else
    printf '%s\n' "OPO Monitoring Service is stopped."
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
  status)
    status_service
    ;;
  restart)
    stop_service || true
    start_service
    ;;
  run)
    find_python
    exec "$PYTHON" -m uvicorn ApplicationUI.analytics_agents.opo_monitoring_service.api:app \
      --host "${ASML_AI_HOST:-127.0.0.1}" \
      --port "${ASML_AI_PORT:-8000}"
    ;;
  *)
    printf '%s\n' "Usage: $0 {start|stop|restart|status|run}" >&2
    exit 2
    ;;
esac
