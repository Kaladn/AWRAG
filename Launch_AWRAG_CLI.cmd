@echo off
setlocal
set "PACKAGE_ROOT=%~dp0"
powershell.exe -NoExit -ExecutionPolicy Bypass -File "%PACKAGE_ROOT%Start_AWRAG_CLI.ps1"
