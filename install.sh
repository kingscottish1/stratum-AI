#!/usr/bin/env bash
# ============================================================
#  Stratum AI - one-time installer (Linux / macOS)
#  Built by kingscottishDEV / N.A.S - Nexus Audit Security
#  Usage: bash install.sh   (or: ./install.sh)
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

echo
echo " ============================================"
echo "  Stratum AI - Installer (Linux / macOS)"
echo " ============================================"
echo

# ---- locate python ----------------------------------------------------------
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo " [ERROR] Python 3.10+ not found."
  echo "         macOS:  brew install python"
  echo "         Ubuntu: sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

if ! "$PY" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"; then
  echo " [ERROR] Python 3.10 or newer is required (found: $("$PY" --version 2>&1))."
  exit 1
fi
echo " [OK] $("$PY" --version 2>&1)"

# ---- virtual environment ----------------------------------------------------
if [ ! -x ".venv/bin/python" ]; then
  echo " [..] Creating virtual environment..."
  "$PY" -m venv .venv
else
  echo " [OK] Virtual environment already exists"
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# ---- dependencies -------------------------------------------------------------
echo " [..] Installing dependencies (first run takes a few minutes)..."
python -m pip install --upgrade pip -q
pip install -q -r requirements.txt -r requirements-dev.txt
echo " [OK] Dependencies installed"

# ---- .env ------------------------------------------------------------------------
if [ ! -f ".env" ]; then
  echo " [..] Generating .env with fresh secrets (DEMO_MODE=ON for testing)..."
  python scripts/generate_env.py
else
  echo " [OK] .env already exists - keeping it"
fi

cat <<'EOF'

 ============================================
  INSTALL COMPLETE
 ============================================

 Next steps:
  1) bash run.sh               (or: ./run.sh)
  2) Your browser opens http://localhost:8000
  3) Click "Create account" - the first account is the owner
  4) On the dashboard click "load demo data" (demo mode)
  5) Open the Agents console and send a message

 Optional - bring your own LLM (edit .env):
  LLM_PROVIDER=openai
  LLM_API_KEY=sk-...
  then set DEMO_MODE=false for real mode.
EOF
