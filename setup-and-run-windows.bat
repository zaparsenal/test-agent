@echo off
setlocal
cd /d "%~dp0"
title FieldGuide Setup and Demo

echo.
echo FieldGuide Windows Setup
echo ========================
echo.

set "PYTHON_LAUNCH="

where py >nul 2>nul
if not errorlevel 1 (
  py -3.14 -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 14) else 1)" >nul 2>nul
  if not errorlevel 1 set "PYTHON_LAUNCH=py -3.14"
)

if not defined PYTHON_LAUNCH (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 14) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_LAUNCH=python"
  )
)

if not defined PYTHON_LAUNCH (
  echo [ERROR] Python 3.14 was not found.
  echo Install Python 3.14 from https://www.python.org/downloads/windows/
  goto :failed
)

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found.
  echo Install Node.js 22.13 or newer from https://nodejs.org/
  goto :failed
)

node -e "const [major, minor] = process.versions.node.split('.').map(Number); process.exit(major > 22 || (major === 22 && minor >= 13) ? 0 : 1)"
if errorlevel 1 (
  echo [ERROR] FieldGuide needs Node.js 22.13 or newer.
  echo Install the current LTS release from https://nodejs.org/
  goto :failed
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm was not found. Reinstall Node.js from https://nodejs.org/
  goto :failed
)

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 14) else 1)" >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] The existing .venv folder was created with a different Python version.
    echo Rename or remove .venv, then run this file again.
    goto :failed
  )
) else (
  echo [1/4] Creating the Python 3.14 environment...
  %PYTHON_LAUNCH% -m venv .venv
  if errorlevel 1 goto :failed
)

echo [2/4] Installing Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [3/4] Installing web packages...
call npm install
if errorlevel 1 goto :failed

echo [4/4] Checking the installation...
call npm run test
if errorlevel 1 goto :failed

echo.
echo Setup complete. FieldGuide is starting now.
echo Keep this window open while using the demo.
echo Press Ctrl+C when you want to stop it.
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 5; Start-Process 'http://localhost:3000'"
call npm run demo
goto :finished

:failed
echo.
echo Setup could not finish. Read the error above, then run this file again.
pause
exit /b 1

:finished
endlocal
