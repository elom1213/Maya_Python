@echo off
rem ============================================================================
rem  A00490_KeyboardTool - double-click to open the tool
rem  Python Script by Ji Hun Park / last Update date : 2026-10-26
rem
rem  The tool is a PySide6 app that runs outside Maya. It only needs 64-bit
rem  Python 3.10+ with PySide6 (key sending is ctypes, standard library).
rem  How a Python is picked, in this order:
rem    1) the tool's own environment  %USERPROFILE%\.jun_keyboardtool\venv
rem    2) an installed Python that already has PySide6: py -3.14 .. -3.10, then
rem       python on PATH (the Microsoft Store shortcut is skipped). Each one is
rem       RUN and its version read - "py -3.12" prints an error but exits 0 when
rem       that version is missing. Nothing is installed in this case.
rem    3) none has PySide6: builds 1) from the newest 64-bit Python 3.10+
rem       (venv + pip install PySide6-Essentials, once per PC, 1 - 2 minutes).
rem       The environment is outside the tool folder on purpose: the PySide6
rem       wheel has a 151-character path, a deep tool folder breaks the 260 limit.
rem  Then the window opens with pythonw (no console).
rem  Options: --setup (build / repair the environment), --force (rebuild it),
rem  --console (run with python.exe so errors stay on screen), --no-launch
rem  (check only, prints READY + the interpreter - for scripts).
rem  Full output of a setup: setup_env.log (this folder).
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
rem Isolate from another install's PYTHONPATH / PYTHONHOME. User site stays on -
rem a "pip install --user PySide6" must still count as "has PySide6".
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "HOME_DIR=%USERPROFILE%\.jun_keyboardtool"
if defined JUN_KEYBOARDTOOL_HOME set "HOME_DIR=%JUN_KEYBOARDTOOL_HOME%"
set "VENV=%HOME_DIR%\venv"
set "VPY=%VENV%\Scripts\python.exe"
set "LOG=%~dp0setup_env.log"
set "PROBE=%TEMP%\jun_a00490_probe.txt"
set "DO_SETUP=0"
set "FORCE=0"
set "NO_LAUNCH=0"
set "CONSOLE=0"
for %%A in (%*) do (
    if /i "%%~A"=="--setup" set "DO_SETUP=1"
    if /i "%%~A"=="--force" (set "DO_SETUP=1" & set "FORCE=1")
    if /i "%%~A"=="--no-launch" set "NO_LAUNCH=1"
    if /i "%%~A"=="--console" set "CONSOLE=1"
)
set "PYEXE="
set "PYW="

if not exist "launch.py" (
    echo [ERROR] launch.py not found - run this file from the A00490_KeyboardTool folder.
    pause
    exit /b 1
)
if "%DO_SETUP%"=="1" goto :setup

rem ---------------------------------------------------- 1) own environment
if exist "%VPY%" (
    call :probe "%VPY%"
    if defined P_READY (
        set "PYEXE=%VPY%"
        goto :launch
    )
    echo The tool environment does not run ^(its Python was removed?^) - rebuilding ...
    set "FORCE=1"
    goto :setup
)

rem ---------------------------------------------------- 2) installed Python with PySide6
for %%V in (3.14 3.13 3.12 3.11 3.10) do (
    if not defined PYEXE call :try_cmd "py -%%V"
)
if defined PYEXE goto :launch
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYEXE call :try_path "%%P"
)
if defined PYEXE goto :launch

rem ---------------------------------------------------- 3) build the environment
echo First run - no Python with PySide6 found. Preparing the tool environment ^(once per PC, 1 - 2 minutes^) ...
goto :setup

rem ============================================================================
:setup
> "%LOG%" echo A00490_KeyboardTool setup - %DATE% %TIME%
call :say "============================================================"
call :say " A00490_KeyboardTool - environment setup"
call :say " Folder: %CD%"
call :say " Env:    %VENV%"
call :say "============================================================"
if not exist "%HOME_DIR%" mkdir "%HOME_DIR%" >> "%LOG%" 2>&1
if not exist "%HOME_DIR%" (
    call :say "[ERROR] Cannot create %HOME_DIR% - set JUN_KEYBOARDTOOL_HOME to a short writable folder (e.g. C:\JUN)."
    goto :end_fail
)
if not exist "Framework\qt\qt.py" if not exist "..\..\Framework\qt\qt.py" (
    call :say "[ERROR] Framework not found - the tool folder is incomplete (needs Framework\ or ..\..\Framework\)."
    goto :end_fail
)

call :say ""
call :say "[1/4] Looking for 64-bit Python 3.10 or newer ..."
set "BASE="
set "BASEVER="
set "OTHERS="
for %%V in (3.14 3.13 3.12 3.11 3.10) do (
    if not defined BASE call :base_cmd "py -%%V"
)
if not defined BASE (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        if not defined BASE call :base_path "%%P"
    )
)
if not defined BASE (
    call :say "[ERROR] 64-bit Python 3.10 or newer is required.%OTHERS%"
    call :say "        Install it from https://www.python.org/downloads/windows/ and run this file again."
    goto :end_fail
)
call :say "      found: %BASE%  (Python %BASEVER%)"

call :say ""
call :say "[2/4] Preparing the environment %VENV% ..."
if "%FORCE%"=="1" if exist "%VENV%" (
    call :say "      --force: removing the old venv"
    rmdir /s /q "%VENV%"
)
if exist "%VPY%" (
    call :probe "%VPY%"
    if not defined P_OK (
        call :say "      existing venv does not run or uses an unsupported Python - rebuilding"
        rmdir /s /q "%VENV%"
    ) else (
        call :say "      reusing the existing venv"
    )
) else if exist "%VENV%" (
    call :say "      removing a broken venv (no python.exe)"
    rmdir /s /q "%VENV%"
)
if not exist "%VPY%" (
    call %BASE% -m venv "%VENV%" >> "%LOG%" 2>&1
    if not exist "%VPY%" (
        call :say "[ERROR] Could not create the venv - see setup_env.log"
        goto :end_fail
    )
    call :say "      created venv"
)

call :say ""
call :say "[3/4] Installing PySide6 Essentials (about 90 MB) ..."
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
"%VPY%" -m pip install PySide6-Essentials >> "%LOG%" 2>&1
if errorlevel 1 goto :pip_fail
"%VPY%" -c "import PySide6.QtWidgets" >> "%LOG%" 2>&1
if errorlevel 1 goto :pip_fail
call :say "      packages OK"

call :say ""
call :say "[4/4] Self test (imports, builds the window offscreen) ..."
set "ST=%TEMP%\jun_a00490_selftest.txt"
"%VPY%" "app\selftest.py" > "%ST%" 2>> "%LOG%"
set "STRC=%ERRORLEVEL%"
type "%ST%"
type "%ST%" >> "%LOG%"
del "%ST%" >nul 2>&1
if not "%STRC%"=="0" (
    call :say "[ERROR] Self test failed - see the message above and setup_env.log"
    goto :broken_env
)
call :say "============================================================"
call :say " SETUP OK - next time this file opens the window directly"
call :say "============================================================"
set "PYEXE=%VPY%"
goto :launch

:pip_fail
rem tail first, then log the line - otherwise the tail shows this very line
echo [ERROR] Package installation failed. Last lines of setup_env.log:
powershell -NoProfile -Command "Get-Content -Tail 15 -LiteralPath '%LOG%'"
>> "%LOG%" echo [ERROR] Package installation failed.
findstr /i /c:"No matching distribution" "%LOG%" >nul && call :say "  - Hint: no PySide6 wheel for Python %BASEVER% yet - install Python 3.12 / 3.13 and run again."
findstr /i /c:"No such file or directory" /c:"path too long" /c:"WinError 3]" /c:"Long Path" "%LOG%" >nul && call :say "  - Hint: Windows 260-character path limit - set JUN_KEYBOARDTOOL_HOME to a short folder (e.g. C:\JUN) and run again."
findstr /i /c:"SSL" /c:"timed out" /c:"ProxyError" "%LOG%" >nul && call :say "  - Hint: network / proxy problem. Check the internet connection or set a pip proxy."

:broken_env
rem a half-installed venv may still import QtWidgets and would pass as "ready" next time - remove it
if exist "%VENV%" (
    call :say "      removing the incomplete environment %VENV%"
    rmdir /s /q "%VENV%"
)
goto :end_fail

:end_fail
call :say ""
call :say "SETUP FAILED - full log: %LOG%"
if "%NO_LAUNCH%"=="0" pause
exit /b 1

rem ============================================================================
:launch
rem pythonw.exe sits next to python.exe (system install and venv alike). Without it
rem the console flashes but the tool still runs.
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
rem  helpers
rem ---------------------------------------------------------------------------
:try_cmd
rem a "py -3.xx" command: usable for launching only when it has PySide6
call :probe "%~1"
if defined P_READY set "PYEXE=%P_EXE%"
exit /b 0

:try_path
echo %~1 | find /i "WindowsApps" >nul
if not errorlevel 1 exit /b 0
call :probe "%~1"
if defined P_READY set "PYEXE=%P_EXE%"
exit /b 0

:base_cmd
rem a "py -3.xx" command: usable as venv base when it is 64-bit 3.10+
call :probe "%~1"
if defined P_OK (
    set "BASE=%~1"
    set "BASEVER=%P_VER%"
) else if defined P_VER (
    call :note_other "%P_VER%"
)
exit /b 0

:base_path
echo %~1 | find /i "WindowsApps" >nul
if not errorlevel 1 exit /b 0
call :probe "%~1"
if defined P_OK (
    set "BASE="%~1""
    set "BASEVER=%P_VER%"
) else if defined P_VER (
    call :note_other "%P_VER%"
)
exit /b 0

:note_other
echo "%OTHERS%" | find "%~1" >nul
if errorlevel 1 set "OTHERS=%OTHERS% Found Python %~1 (not usable: needs 3.10+ 64-bit)."
exit /b 0

:probe
rem Runs the interpreter and reads what it prints. Sets
rem   P_VER   e.g. 3.11          P_EXE  its python.exe (sys.executable)
rem   P_OK    64-bit 3.10+       P_READY  P_OK and PySide6.QtWidgets imports
rem  %~1 = "py -3.14" (command) or a full path to python.exe
set "P_OK="
set "P_READY="
set "P_VER="
set "P_EXE="
set "P_LINE="
if exist "%~1" (
    "%~1" -c "import sys; print('JUNPY', *sys.version_info[:2], 64 if sys.maxsize > 2**32 else 32, sys.executable)" > "%PROBE%" 2>nul
) else (
    call %~1 -c "import sys; print('JUNPY', *sys.version_info[:2], 64 if sys.maxsize > 2**32 else 32, sys.executable)" > "%PROBE%" 2>nul
)
if exist "%PROBE%" set /p P_LINE=<"%PROBE%"
del "%PROBE%" >nul 2>&1
if not defined P_LINE exit /b 0
for /f "tokens=1-4*" %%a in ("%P_LINE%") do (
    if "%%a"=="JUNPY" (
        set "P_VER=%%b.%%c"
        set "P_EXE=%%e"
        if "%%b"=="3" if "%%d"=="64" if %%c GEQ 10 set "P_OK=1"
    )
)
if not defined P_OK exit /b 0
if not defined P_EXE exit /b 0
rem a real import (not find_spec): a broken PySide6 (missing VC++ runtime) must not count
"%P_EXE%" -c "import PySide6.QtWidgets" >nul 2>&1
if not errorlevel 1 set "P_READY=1"
exit /b 0

:say
echo(%~1
>> "%LOG%" echo(%~1
exit /b 0
