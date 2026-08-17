#!/usr/bin/env bash
# Stratum AI — bootstrap .env with freshly generated secrets.
# Thin wrapper around the cross-platform generator (works on Windows too).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/generate_env.py
