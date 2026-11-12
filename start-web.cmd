@echo off
setlocal
title SME Knowledge Copilot - Start
rem Default: read Gemini settings from .env. Use -NoAI for local checks without Gemini.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\web-dev.ps1" -Action Start %*
set "SME_WEB_EXIT=%ERRORLEVEL%"
if not "%SME_WEB_EXIT%"=="0" (
  echo.
  echo Web could not start. Read the message above and the log folder.
  if not defined SME_WEB_NO_PAUSE pause
)
exit /b %SME_WEB_EXIT%
