@echo off
rem ============================================================================
rem  A00560_JaliBatch - double-click to open the tool
rem  Python Script by Ji Hun Park / last Update date : 2026-10-26
rem
rem  First run: builds the environment (%USERPROFILE%\.jun_jalibatch\venv + PySide6,
rem  see setup_env.bat) then opens the window. Later runs: opens the window directly
rem  (no console). The environment is outside the tool folder on purpose - the PySide6
rem  wheel has a 151-character path, so a deep tool folder would break the 260 limit.
rem  Works with Windows 10 / 11 and any 64-bit Python 3.10+ (3.14 included); with
rem  no usable Python it offers to download a private one. Maya itself is only
rem  needed for mayapy (set inside the tool).
rem  Options: --setup (run the setup again), --force (rebuild the venv), --no-launch
rem  (check only, for scripts).
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"
set "HOME_DIR=%USERPROFILE%\.jun_jalibatch"
if defined JUN_JALIBATCH_HOME set "HOME_DIR=%JUN_JALIBATCH_HOME%"
set "VPYW=%HOME_DIR%\venv\Scripts\pythonw.exe"
set "VPY=%HOME_DIR%\venv\Scripts\python.exe"
set "DO_SETUP=0"
set "SETUP_ARGS=--nopause"
set "NO_LAUNCH=0"
for %%A in (%*) do (
    if /i "%%~A"=="--setup" set "DO_SETUP=1"
    if /i "%%~A"=="--force" (set "DO_SETUP=1" & set "SETUP_ARGS=--nopause --force")
    if /i "%%~A"=="--no-launch" set "NO_LAUNCH=1"
    if /i "%%~A"=="--yes" set "SETUP_ARGS=%SETUP_ARGS% --yes"
)

if "%DO_SETUP%"=="1" goto :setup
if not exist "%VPYW%" (
    echo First run - preparing the environment ^(a few minutes, once per PC^) ...
    goto :setup
)
rem the venv points at the Python it was made from (absolute path) - removing that Python
rem breaks it, and pythonw would fail silently. Check with a console first.
"%VPY%" -c "import PySide6, sys; sys.exit(0)" >nul 2>&1
if errorlevel 1 (
    echo The environment does not run ^(its Python was removed?^) - rebuilding ...
    set "SETUP_ARGS=--nopause --force"
    goto :setup
)
goto :launch

:setup
call "%~dp0setup_env.bat" %SETUP_ARGS%
if errorlevel 1 (
    echo.
    echo [ERROR] Setup failed - see setup_env.log in this folder.
    if "%NO_LAUNCH%"=="0" pause
    exit /b 1
)
if not exist "%VPYW%" (
    echo [ERROR] Setup finished but %VPYW% is missing - see setup_env.log
    if "%NO_LAUNCH%"=="0" pause
    exit /b 1
)

:launch
if "%NO_LAUNCH%"=="1" (
    echo READY - %VPYW%
    exit /b 0
)
start "" "%VPYW%" "%~dp0launch.py"
exit /b 0
