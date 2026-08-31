@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Install-ContentOpsV1SimpleScheduler.ps1" %*
exit /b %errorlevel%
