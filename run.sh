#!/usr/bin/env bash
# ============================================================
#  Stratum AI - start the app (Linux / macOS)
#  Built by kingscottishDEV / N.A.S - Nexus Audit Security
#  Usage: bash run.sh   (or: ./run.sh)
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo " [ERROR] Not installed yet. Run: bash install.sh"
  exit 1
fi
if [ ! -f ".env" ]; then
  echo " [ERROR] No .env found. Run: bash install.sh"
  exit 1
fi

source .venv/bin/activate
export PYTHONUTF8=1

echo
echo " Starting Stratum AI..."
echo "  App:       http://localhost:8000"
echo "  API docs:  http://localhost:8000/docs"
echo "  Press Ctrl+C to stop."
echo

# open the browser after a short delay so the server is ready
( sleep 5
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:8000 >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open http://localhost:8000 >/dev/null 2>&1 || true
  fi ) &

exec python -m uvicorn CORE_AGENT_INFRASTRUCTURE.api.main:app --host 127.0.0.1 --port 8000
