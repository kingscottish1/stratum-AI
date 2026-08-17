@echo off
REM Stratum AI - run the test suite (Windows)
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo  [ERROR] Run install.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
set "PYTHONUTF8=1"
python -m pytest tests/ -v
pause
