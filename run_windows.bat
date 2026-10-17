@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo QuantumScope is not installed yet. Run install_and_run_windows.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m quantumscope
if errorlevel 1 pause
