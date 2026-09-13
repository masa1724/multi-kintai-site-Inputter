@echo off
setlocal
set "app=%~dp0desktop\build\bin\desktop.exe"
if not exist "%app%" (
  echo Wails app not found: "%app%"
  echo Run "wails build" in the desktop directory first.
  exit /b 1
)
start "" /D "%~dp0desktop" "%app%"
exit /b %errorlevel%
