@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
echo Deze installer is alleen bedoeld voor ontwikkeling met Python-broncode.
echo Voor normaal gebruik kies:
echo   %PROJECT_ROOT%release\0.1\Install-AfbeeldingenNaarJPG-Standalone.cmd
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File "%PROJECT_ROOT%install-from-git.ps1"
exit /b %ERRORLEVEL%
