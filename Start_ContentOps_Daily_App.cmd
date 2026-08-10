@echo off
setlocal
title Capital Chronicle ContentOps V1 - Daily App

rem One-click morning entry point. Double-click to safely start or resume the
rem canonical ContentOps Daily App. Safe to run repeatedly: it never starts a
rem duplicate supervisor, never resets the durable store, never clears the kill
rem switch, and fails closed if the port owner cannot be proven.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-ContentOpsDailyApp.ps1" %*
set LAUNCH_EXIT=%ERRORLEVEL%

echo.
if "%1"=="" pause
exit /b %LAUNCH_EXIT%
