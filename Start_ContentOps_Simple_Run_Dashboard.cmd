@echo off
setlocal
title Capital Chronicle ContentOps V1 - Simple Run Monitor

rem One-click nontechnical run monitor. Starts/resumes the canonical Daily App
rem without opening the technical console, then opens the read-only simple view.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-ContentOpsSimpleRunDashboard.ps1" %*
set LAUNCH_EXIT=%ERRORLEVEL%

echo.
if "%1"=="" pause
exit /b %LAUNCH_EXIT%
