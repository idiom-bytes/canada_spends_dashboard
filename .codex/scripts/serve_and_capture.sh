#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
URL="${URL:-http://localhost:${PORT}/index.html}"
OUTPUT="${OUTPUT:-artifacts/dashboard.png}"
DELAY_MS="${DELAY_MS:-1000}"

python -m http.server "${PORT}" >/tmp/dashboard_server.log 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "${SERVER_PID}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

sleep 1
python .codex/scripts/capture_dashboard.py --url "${URL}" --output "${OUTPUT}" --delay-ms "${DELAY_MS}"
echo "Screenshot saved to ${OUTPUT}"
