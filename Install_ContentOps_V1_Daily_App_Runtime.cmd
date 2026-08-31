@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Install-ContentOpsV1DailyAppRuntime.ps1" %*
exit /b %ERRORLEVEL%
