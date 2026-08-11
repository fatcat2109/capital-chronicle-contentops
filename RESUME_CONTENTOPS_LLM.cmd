@echo off
setlocal
title Capital Chronicle ContentOps - Resume LLM

rem Explicitly clears only the persistent operator LLM pause. It does not start the app.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Resume-ContentOpsLLM.ps1" %*
set RESUME_EXIT=%ERRORLEVEL%

echo.
if "%1"=="" pause
exit /b %RESUME_EXIT%
