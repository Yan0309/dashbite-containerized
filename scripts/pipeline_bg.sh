#!/usr/bin/env bash
# Durable background start/stop for DashBite pipeline stages.
# Used by `make run` / `make stop` so processes outlive the Make recipe shell.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG_DIR="${LOG_DIR:-$ROOT/.logs}"
PIDS="${PIDS:-$LOG_DIR/pids}"
PY="${PY:-$ROOT/.venv/bin/python}"
STREAMLIT="${STREAMLIT:-$ROOT/.venv/bin/streamlit}"
export PYTHONPATH="${PYTHONPATH:-$ROOT}"
export PYTHONUNBUFFERED=1

mkdir -p "$LOG_DIR" "$PIDS"

start_one() {
  local name="$1"
  shift
  # Kill any stale process for this name before restarting.
  if [[ -f "$PIDS/$name.pid" ]]; then
    local old
    old="$(cat "$PIDS/$name.pid" 2>/dev/null || true)"
    if [[ -n "${old:-}" ]]; then
      kill "$old" 2>/dev/null || true
      pkill -P "$old" 2>/dev/null || true
    fi
    rm -f "$PIDS/$name.pid"
  fi

  nohup "$@" >"$LOG_DIR/$name.log" 2>&1 </dev/null &
  local pid=$!
  echo "$pid" >"$PIDS/$name.pid"
  disown "$pid" 2>/dev/null || true
  sleep 0.3
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "error: $name failed to stay up — see $LOG_DIR/$name.log" >&2
    tail -n 40 "$LOG_DIR/$name.log" >&2 || true
    return 1
  fi
  echo "started $name pid=$pid"
}

cmd_start() {
  start_one simulator "$PY" -m pipeline.simulator
  start_one preprocess "$PY" -m pipeline.preprocess
  start_one train "$PY" -m pipeline.train
  start_one infer "$PY" -m pipeline.infer
  start_one dashboard env PYTHONPATH="$ROOT" "$STREAMLIT" run pipeline/dashboard/app.py \
    --server.headless true --server.port 8501
  echo ""
  echo "Dashboard (Model Pulse): http://localhost:8501"
  echo "Logs: $LOG_DIR/   PIDs: $PIDS/"
  echo "Stop with: make stop"
}

cmd_stop() {
  if [[ -d "$PIDS" ]]; then
    for f in "$PIDS"/*.pid; do
      [[ -f "$f" ]] || continue
      local pid name
      pid="$(cat "$f")"
      name="$(basename "$f" .pid)"
      if [[ -n "$pid" ]]; then
        kill "$pid" 2>/dev/null || true
        pkill -P "$pid" 2>/dev/null || true
        # Streamlit sometimes needs a second signal.
        sleep 0.2
        kill -9 "$pid" 2>/dev/null || true
      fi
      rm -f "$f"
      echo "stopped $name"
    done
  fi
  # Sweep leftovers from older launches / orphaned children.
  pkill -f "$ROOT/.venv/bin/python -m pipeline.simulator" 2>/dev/null || true
  pkill -f "$ROOT/.venv/bin/python -m pipeline.preprocess" 2>/dev/null || true
  pkill -f "$ROOT/.venv/bin/python -m pipeline.train" 2>/dev/null || true
  pkill -f "$ROOT/.venv/bin/python -m pipeline.infer" 2>/dev/null || true
  pkill -f "streamlit run pipeline/dashboard/app.py" 2>/dev/null || true
  echo "Pipeline stopped."
}

cmd_status() {
  local any=0
  for name in simulator preprocess train infer dashboard; do
    local f="$PIDS/$name.pid"
    if [[ -f "$f" ]]; then
      local pid
      pid="$(cat "$f")"
      if kill -0 "$pid" 2>/dev/null; then
        echo "UP   $name pid=$pid"
        any=1
      else
        echo "DOWN $name (stale pid file)"
      fi
    else
      echo "DOWN $name"
    fi
  done
  if [[ "$any" -eq 0 ]]; then
    return 1
  fi
}

case "${1:-}" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  status) cmd_status ;;
  *)
    echo "Usage: $0 {start|stop|status}" >&2
    exit 2
    ;;
esac
