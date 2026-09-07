@echo off
setlocal
cd /d "%~dp0"
title FieldGuide Setup and Demo

where npm >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] Node.js was not found.
  echo Install Node.js 22.13 or newer from https://nodejs.org/
  echo Then run this file again.
  echo.
  pause
  exit /b 1
)

call npm run setup
if errorlevel 1 (
  echo.
  echo FieldGuide stopped because setup or startup did not finish.
  echo Read the error above, correct it, and run this file again.
  echo.
  pause
  exit /b 1
)

endlocal
