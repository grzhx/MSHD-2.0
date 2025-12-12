#!/usr/bin/env bash
# Unified launcher for the disaster management system (backend + frontend).
# - Starts FastAPI backend on port 8000 using the existing .venv in access-storage (creates it if missing)
# - Starts Angular frontend dev server on port 3000
# Logs are written to .run-logs/backend.log and .run-logs/frontend.log

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/access-storage"
FRONTEND_DIR="$ROOT/disaster-management-dashboard"
LOG_DIR="$ROOT/.run-logs"
mkdir -p "$LOG_DIR"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

echo "[launcher] ensuring backend venv and deps..."
if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi
"$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt" >/dev/null

echo "[launcher] starting backend on http://localhost:8000 ..."
(
  cd "$BACKEND_DIR"
  exec "$BACKEND_DIR/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --log-level info --reload
) >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo "[launcher] ensuring frontend deps..."
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "[launcher] starting frontend dev server on http://localhost:3000 ..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev -- --host 0.0.0.0 --port 3000
) >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "[launcher] backend pid=$BACKEND_PID log=$LOG_DIR/backend.log"
echo "[launcher] frontend pid=$FRONTEND_PID log=$LOG_DIR/frontend.log"
echo "[launcher] press Ctrl+C to stop both. Tail logs with: tail -f $LOG_DIR/backend.log $LOG_DIR/frontend.log"

wait
