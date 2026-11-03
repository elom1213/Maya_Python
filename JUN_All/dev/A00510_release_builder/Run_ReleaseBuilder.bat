@echo off
rem ============================================================================
rem  A00510_release_builder - double-click to open the Release Builder
rem  Python Script by Ji Hun Park / last Update date : 2026-11-03
rem
rem  Runs the tool outside Maya with an installed 64-bit Python 3.7+ that has
rem  PySide6 (or PySide2). Nothing is installed. Picked in this order:
rem    py -3.14 .. -3.7, then python on PATH (Microsoft Store shortcut skipped).
rem  Every run also makes / refreshes "Release Builder.lnk" in this folder - a
rem  shortcut with the tool icon (a .bat file cannot have its own icon). Use the
rem  shortcut afterwards if you want the icon in Explorer or on the taskbar.
rem  Options: --console (python.exe, errors stay on screen), --shortcut (rebuild
rem  the shortcut), --no-launch (find Python + shortcut only).
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PROBE=%TEMP%\jun_a00510_probe.txt"
set "CONSOLE=0"
set "FORCE_LNK="
set "NO_LAUNCH=0"
for %%A in (%*) do (
    if /i "%%~A"=="--console" set "CONSOLE=1"
    if /i "%%~A"=="--shortcut" set "FORCE_LNK=--force"
    if /i "%%~A"=="--no-launch" set "NO_LAUNCH=1"
)
set "PYEXE="

if not exist "launch.py" (
    echo [ERROR] launch.py not found - run this file from the A00510_release_builder folder.
    pause
    exit /b 1
)

for %%V in (3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7) do (
    if not defined PYEXE call :try_cmd "py -%%V"
)
if not defined PYEXE (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        if not defined PYEXE call :try_path "%%P"
    )
)
if not defined PYEXE (
    echo [ERROR] No Python with PySide6 / PySide2 found.
    echo         Install 64-bit Python 3.10+ and run:  py -m pip install PySide6
    pause
    exit /b 1
)

rem shortcut with the tool icon - failure is reported but does not stop the tool
"%PYEXE%" "%~dp0make_shortcut.py" %FORCE_LNK%
if errorlevel 1 echo [WARN] Could not make the shortcut - the tool still opens.

set "PYW=%PYEXE:python.exe=pythonw.exe%"
if not exist "%PYW%" set "PYW=%PYEXE%"
if "%NO_LAUNCH%"=="1" (
    echo READY - %PYW%
    exit /b 0
)
if "%CONSOLE%"=="1" (
    "%PYEXE%" "%~dp0launch.py"
    if errorlevel 1 pause
    exit /b 0
)
start "" "%PYW%" "%~dp0launch.py"
exit /b 0

rem ---------------------------------------------------------------------------
:try_cmd
call :probe "%~1"
exit /b 0

:try_path
echo %~1 | find /i "WindowsApps" >nul
if not errorlevel 1 exit /b 0
call :probe "%~1"
exit /b 0

:probe
rem sets PYEXE to sys.executable when the interpreter runs, is 64-bit and imports Qt
set "P_LINE="
set "P_EXE="
if exist "%~1" (
    "%~1" -c "import sys; print('JUNPY', 64 if sys.maxsize > 2**32 else 32, sys.executable)" > "%PROBE%" 2>nul
) else (
    call %~1 -c "import sys; print('JUNPY', 64 if sys.maxsize > 2**32 else 32, sys.executable)" > "%PROBE%" 2>nul
)
if exist "%PROBE%" set /p P_LINE=<"%PROBE%"
del "%PROBE%" >nul 2>&1
if not defined P_LINE exit /b 0
for /f "tokens=1,2*" %%a in ("%P_LINE%") do (
    if "%%a"=="JUNPY" if "%%b"=="64" set "P_EXE=%%c"
)
if not defined P_EXE exit /b 0
rem a real import (not find_spec): a broken PySide (missing VC++ runtime) must not count
"%P_EXE%" -c "exec('try:\n import PySide6.QtWidgets\nexcept ImportError:\n import PySide2.QtWidgets')" >nul 2>&1
if errorlevel 1 exit /b 0
set "PYEXE=%P_EXE%"
exit /b 0
