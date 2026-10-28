@echo off
"%~dp0bin\assis-setup.exe" uninstall %*
exit /b %errorlevel%
