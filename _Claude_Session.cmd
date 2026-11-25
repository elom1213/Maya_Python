@echo off
rem Double-click to open a Claude Code session rooted at this folder.
rem Portable: no hard-coded paths. Works from any PC / drive / junction / UNC share.
rem Extra arguments are passed through to claude (e.g. -c to continue, -p "..." for a one-shot).
setlocal

rem pushd (not cd /d) so UNC network paths also work - it maps a temporary drive letter.
pushd "%~dp0" || (echo [Claude_Session] Cannot enter "%~dp0". & pause & exit /b 1)
title Claude - %CD%

rem Locate claude: PATH first, then the default native-installer location.
set "CLAUDE_EXE="
where claude >nul 2>&1 && set "CLAUDE_EXE=claude"
if not defined CLAUDE_EXE if exist "%USERPROFILE%\.local\bin\claude.exe" set "CLAUDE_EXE=%USERPROFILE%\.local\bin\claude.exe"
if not defined CLAUDE_EXE (
  echo [Claude_Session] Claude Code not found on this PC.
  echo Install it, then run this file again:
  echo   powershell -c "irm https://claude.ai/install.ps1 | iex"
  pause
  popd
  exit /b 1
)

"%CLAUDE_EXE%" %*
set "RC=%errorlevel%"
popd
if not "%RC%"=="0" (
  echo.
  echo [Claude_Session] claude exited with error %RC%.
  pause
)
exit /b %RC%
