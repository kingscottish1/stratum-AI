@echo off
REM ============================================================
REM  Stratum AI - one-time installer (Windows)
REM  Built by kingscottishDEV / N.A.S - Nexus Audit Security
REM  Usage: double-click install.bat  (or run: install.bat)
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo  ============================================
echo   Stratum AI - Installer (Windows)
echo  ============================================
echo.

REM ---- locate Python (python, then py launcher) ----------------------
set "PY=python"
%PY% --version >nul 2>nul
if errorlevel 1 set "PY=py -3"
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo  [ERROR] Python 3.10+ was not found.
  echo          Install it from https://www.python.org/downloads/
  echo          and tick "Add python.exe to PATH", then re-run.
  pause
  exit /b 1
)

%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo  [ERROR] Python 3.10 or newer is required.
  pause
  exit /b 1
)
echo  [OK] Python found (3.10+)

REM ---- virtual environment ---------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo  [..] Creating virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo  [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
  )
) else (
  echo  [OK] Virtual environment already exists
)

call ".venv\Scripts\activate.bat"

REM ---- dependencies -------------------------------------------------------
echo  [..] Installing dependencies (first run takes a few minutes)...
python -m pip install --upgrade pip -q
pip install -q -r requirements.txt -r requirements-dev.txt
if errorlevel 1 (
  echo  [ERROR] Dependency installation failed.
  pause
  exit /b 1
)
echo  [OK] Dependencies installed

REM ---- .env ------------------------------------------------------------------
if not exist ".env" (
  echo  [..] Generating .env with fresh secrets (DEMO_MODE=ON for testing)...
  python scripts\generate_env.py
  if errorlevel 1 (
    echo  [ERROR] Could not create .env
    pause
    exit /b 1
  )
) else (
  echo  [OK] .env already exists - keeping it
)

echo.
echo  ============================================
echo   INSTALL COMPLETE
echo  ============================================
echo.
echo   Next steps:
echo    1) Double-click run.bat   (or type: run.bat)
echo    2) Your browser opens http://localhost:8000
echo    3) Click "Create account" - the first account is the owner
echo    4) On the dashboard click "load demo data" (demo mode)
echo    5) Open the Agents console and send a message
echo.
echo   Optional - bring your own LLM (edit .env):
echo     LLM_PROVIDER=openai
echo     LLM_API_KEY=sk-...
echo     then set DEMO_MODE=false for real mode.
echo.
pause
