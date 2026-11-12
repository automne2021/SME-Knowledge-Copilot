@echo off
setlocal
title SME Knowledge Copilot - Stop
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\web-dev.ps1" -Action Stop %*
set "SME_WEB_EXIT=%ERRORLEVEL%"
if not "%SME_WEB_EXIT%"=="0" (
  echo.
  echo Some services could not stop. Read the message above.
  if not defined SME_WEB_NO_PAUSE pause
)
exit /b %SME_WEB_EXIT%
