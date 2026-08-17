#!/usr/bin/env bash
# Stratum AI — quick health check for local stacks
API="${1:-http://localhost:8000}"
PORTAL="${2:-http://localhost:8080}"

check() {
  if curl -fsS --max-time 5 "$1" >/dev/null 2>&1; then
    echo "✅ OK   $1"
  else
    echo "❌ FAIL $1"
  fi
}

check "${API}/healthz"
check "${PORTAL}/login"
