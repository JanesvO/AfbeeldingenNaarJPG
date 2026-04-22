@echo off
setlocal
set "SOURCE_ROOT=%~dp0"
powershell -ExecutionPolicy Bypass -NoProfile -File "%SOURCE_ROOT%install-standalone.ps1" -SourceRoot "%SOURCE_ROOT%"
exit /b %ERRORLEVEL%
