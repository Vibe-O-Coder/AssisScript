@echo off
if exist "%~dp0.git" (
  echo Esta e uma copia de desenvolvimento. O binario em bin pode ser historico.
  echo Nao instale bibliotecas novas junto com esse compilador antigo.
  echo Use o pacote completo em build\development-windows-20261102\instalar-windows.cmd.
  echo Para prepara-lo: python tools\prepare-development-installer.py
  exit /b 2
)
"%~dp0bin\assis-setup.exe" install %*
exit /b %errorlevel%
