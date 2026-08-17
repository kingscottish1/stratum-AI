@echo off
REM ============================================================
REM  Stratum AI - start the app (Windows)
REM  Built by kingscottishDEV / N.A.S - Nexus Audit Security
REM  Usage: double-click run.bat  (or type: run.bat)
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo  [ERROR] Not installed yet. Run install.bat first.
  pause
  exit /b 1
)
if not exist ".env" (
  echo  [ERROR] No .env found. Run install.bat first.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

chcp 65001 >nul
set "PYTHONUTF8=1"

echo.
echo  Starting Stratum AI...
echo   App:       http://localhost:8000
echo   API docs:  http://localhost:8000/docs
echo   Press Ctrl+C to stop.
echo.

REM open the browser after a short delay so the server is ready
start "" /b cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8000"

python -m uvicorn CORE_AGENT_INFRASTRUCTURE.api.main:app --host 127.0.0.1 --port 8000

echo.
echo  Server stopped.
pause
