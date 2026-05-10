@echo off
setlocal
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0create_work_record_gui.ps1"
exit /b %errorlevel%
