#!/usr/bin/env bash
# Stratum AI - run the test suite (Linux / macOS)
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/python" ]; then
  echo " [ERROR] Run install.sh first."
  exit 1
fi
source .venv/bin/activate
export PYTHONUTF8=1
python -m pytest tests/ -v
