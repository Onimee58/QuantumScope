@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3.12 -c "import sys" >nul 2>&1
  if not errorlevel 1 (set "QS_PY=py -3.12" & goto :python_ready)
  py -3.13 -c "import sys" >nul 2>&1
  if not errorlevel 1 (set "QS_PY=py -3.13" & goto :python_ready)
  py -3.14 -c "import sys" >nul 2>&1
  if not errorlevel 1 (set "QS_PY=py -3.14" & goto :python_ready)
  py -3.11 -c "import sys" >nul 2>&1
  if not errorlevel 1 (set "QS_PY=py -3.11" & goto :python_ready)
)
where python >nul 2>&1
if errorlevel 1 goto :no_python
set "QS_PY=python"
:python_ready
if exist ".venv\Scripts\python.exe" goto :install
%QS_PY% -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 goto :no_python
echo [1/3] Creating Windows virtual environment...
%QS_PY% -m venv .venv
if errorlevel 1 goto :failure
:install
echo [2/3] Installing QuantumScope dependencies (internet required)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failure
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto :failure
echo [3/3] Launching QuantumScope...
".venv\Scripts\python.exe" -m quantumscope
if errorlevel 1 goto :failure
exit /b 0
:no_python
echo ERROR: Python 3.11+ required. Install Python 3.12 from https://www.python.org/downloads/windows/
echo Select "Add python.exe to PATH" if offered.
goto :failure
:failure
echo.
echo QuantumScope could not complete installation or startup.
pause
exit /b 1
