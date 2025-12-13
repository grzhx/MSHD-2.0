#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/.run-logs"
mkdir -p "$LOG_DIR"

# Mac 常见路径，确保 Homebrew 安装的可执行文件可见
if [[ "$(uname)" == "Darwin" ]]; then
  export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"
fi

PY_BIN="${PY_BIN:-python3}"
NODE_BIN="${NODE_BIN:-node}"
NPM_BIN="${NPM_BIN:-npm}"

# 简单检查端口占用（macOS 使用 lsof）
check_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    if lsof -i tcp:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Port ${port} is already in use. Please free it before continuing."
      exit 1
    fi
  fi
}

# 创建/激活后端虚拟环境并安装依赖
prepare_backend_env() {
  local project_dir="$1"
  local req_file="$2"
  if [[ ! -d "${project_dir}/.venv" ]]; then
    echo "Creating virtualenv in ${project_dir}/.venv"
    (cd "$project_dir" && ${PY_BIN} -m venv .venv)
  fi
  # shellcheck disable=SC1091
  source "${project_dir}/.venv/bin/activate"
  pip install -r "${project_dir}/${req_file}"
}

# 前端安装依赖
prepare_frontend() {
  local project_dir="$1"
  if [[ ! -d "${project_dir}/node_modules" ]]; then
    echo "Installing frontend dependencies..."
    (cd "$project_dir" && ${NPM_BIN} install)
  fi
}

pids=()

cleanup() {
  echo "Stopping services..."
  for pid in "${pids[@]:-}"; do
    if ps -p "$pid" > /dev/null 2>&1; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT

start_service() {
  local name="$1"
  local workdir="$2"
  local cmd="$3"
  local logfile="$4"

  echo "Starting ${name} in ${workdir} -> ${logfile}"
  (
    cd "$workdir"
    exec $cmd
  ) >"$logfile" 2>&1 &
  pids+=($!)
}

# Pre-flight checks
check_port 8000
check_port 8001
check_port 4200

# Backend envs (each service has its own venv to avoid cross pollution)
prepare_backend_env "${ROOT_DIR}/code" "requirements.txt"
CODE_VENV="${ROOT_DIR}/code/.venv/bin"
prepare_backend_env "${ROOT_DIR}/disaster_backend" "requirements.txt"
DISASTER_VENV="${ROOT_DIR}/disaster_backend/.venv/bin"

# Frontend deps
prepare_frontend "${ROOT_DIR}/disaster-management-dashboard"

start_service "codec-service" "${ROOT_DIR}/code" \
  "${CODE_VENV}/uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload" \
  "${LOG_DIR}/codec.log"

start_service "disaster-service" "${ROOT_DIR}/disaster_backend" \
  "${DISASTER_VENV}/uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload" \
  "${LOG_DIR}/disaster.log"

start_service "frontend" "${ROOT_DIR}/disaster-management-dashboard" \
  "${NPM_BIN} start" \
  "${LOG_DIR}/frontend.log"

echo "All services started. Logs in ${LOG_DIR}"
echo "Press Ctrl+C to stop."

wait
