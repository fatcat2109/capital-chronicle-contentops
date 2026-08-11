@echo off
setlocal
title Capital Chronicle ContentOps - EMERGENCY STOP

rem Cost-safety control. The backing script activates the persistent LLM pause fuse
rem before it inventories or stops any proven ContentOps-owned background process.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Stop-ContentOpsBackground.ps1" %*
set STOP_EXIT=%ERRORLEVEL%

echo.
if "%1"=="" pause
exit /b %STOP_EXIT%

