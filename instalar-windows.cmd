@echo off
"%~dp0bin\assis-setup.exe" install %*
exit /b %errorlevel%
