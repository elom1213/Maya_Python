@echo off
rem ============================================================================
rem  A00560_JaliBatch - environment setup  (double-click to run, once per PC)
rem  Python Script by Ji Hun Park / last Update date : 2026-10-26
rem
rem  This tool is a PySide6 app that runs OUTSIDE Maya (Maya work goes to mayapy).
rem  It needs 64-bit Python 3.10 or newer - Python 3.14 is fine (PySide6 ships
rem  abi3 wheels). Windows 10 and 11.
rem  Everything it makes lives in %USERPROFILE%\.jun_jalibatch\ (override with the
rem  JUN_JALIBATCH_HOME environment variable), NOT in the tool folder: the PySide6
rem  wheel contains a 151-character path, so the environment root must stay short
rem  (under about 85 characters) or pip fails with "No such file or directory" on
rem  a PC without Windows long-path support (measured 2026-10-26).
rem  1) find a Python: py launcher (3.14 .. 3.10), python on PATH, or the private
rem     copy in <home>\python\ . Each candidate is RUN and its version read - the
rem     new Python install manager's "py -3.11" prints an error but exits 0 when
rem     that version is not installed (Windows 10 report).
rem  2) none found: offer to download a PRIVATE Python 3.11.9 into <home>\python\
rem     (python.org NuGet package, ~17 MB, SHA-256 checked). Nothing is installed
rem     on the system.
rem  3) create / reuse <home>\venv   4) pip install PySide6 Essentials   5) self
rem     test (opens the window offscreen)   6) Run_JaliBatch.bat is the launcher.
rem  Re-running is safe. Options: --force (rebuild venv), --yes (download without
rem  asking), --nopause (for scripts). Full output: setup_env.log (tool folder)
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
rem Isolate from the PC's own Python / conda (PYTHONPATH of another install would leak in).
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"

set "LOG=%~dp0setup_env.log"
set "HOME_DIR=%USERPROFILE%\.jun_jalibatch"
if defined JUN_JALIBATCH_HOME set "HOME_DIR=%JUN_JALIBATCH_HOME%"
set "VENV=%HOME_DIR%\venv"
set "VPY=%VENV%\Scripts\python.exe"
set "PRIV=%HOME_DIR%\python"
set "PRIV_PY=%PRIV%\python.exe"
set "PRIV_DL=%HOME_DIR%\python_dl"
set "PY_URL=https://www.nuget.org/api/v2/package/python/3.11.9"
set "PY_SHA=9283876d58c017e0e846f95b490da3bca0fc0a6ee1134b2870677cfb7eec3c67"
set "PROBE=%TEMP%\jun_a00560_probe.txt"
set "FORCE=0"
set "NOPAUSE=0"
set "YES=0"
for %%A in (%*) do (
    if /i "%%~A"=="--force" set "FORCE=1"
    if /i "%%~A"=="--nopause" set "NOPAUSE=1"
    if /i "%%~A"=="--yes" set "YES=1"
)

> "%LOG%" echo A00560_JaliBatch setup - %DATE% %TIME%
call :say "============================================================"
call :say " A00560_JaliBatch - environment setup"
call :say " Folder: %CD%"
call :say " Env:    %HOME_DIR%"
call :say "============================================================"
if not exist "%HOME_DIR%" mkdir "%HOME_DIR%" >> "%LOG%" 2>&1
if not exist "%HOME_DIR%" (
    call :say "[ERROR] Cannot create %HOME_DIR% - set JUN_JALIBATCH_HOME to a short writable folder (e.g. C:\JUN)."
    goto :end_fail
)

if not exist "launch.py" (
    call :say "[ERROR] launch.py not found - run this file from the A00560_JaliBatch folder."
    goto :end_fail
)
if not exist "Framework\qt\qt.py" if not exist "..\..\Framework\qt\qt.py" (
    call :say "[ERROR] Framework not found - the tool folder is incomplete (needs Framework\ or ..\..\Framework\)."
    goto :end_fail
)

rem ---------------------------------------------------------------- 1) Python
call :say ""
call :say "[1/5] Looking for 64-bit Python 3.10 or newer (3.14 is fine) ..."
set "PY="
set "PYVER="
set "OTHERS="
call :find_python
if defined PY goto :have_python

call :say "[WARN] No 64-bit Python 3.10+ found.%OTHERS%"
call :say "       This tool can download its own Python 3.11.9 into %PRIV% (about 17 MB)."
call :say "       Nothing is installed on the system."
if "%YES%"=="1" goto :get_private
choice /c YN /m "Download the private Python now"
if errorlevel 2 goto :no_python

:get_private
call :download_python
if errorlevel 1 goto :end_fail
call :probe "%PRIV_PY%"
if defined P_OK (
    set "PY="%PRIV_PY%""
    set "PYVER=%P_VER%"
    goto :have_python
)
call :say "[ERROR] The downloaded Python does not run - see setup_env.log"
goto :end_fail

:no_python
call :say "[ERROR] 64-bit Python 3.10 or newer is required."
call :say "        Run this file again and answer Y to download a private copy, or install Python:"
call :say "        https://www.python.org/downloads/windows/"
goto :end_fail

:have_python
call :say "      found: %PY%  (Python %PYVER%)"

rem ---------------------------------------------------------------- 2) .venv
call :say ""
call :say "[2/5] Preparing the environment %VENV% ..."
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
    call %PY% -m venv "%VENV%" >> "%LOG%" 2>&1
    if not exist "%VPY%" (
        call :say "[ERROR] Could not create the venv - see setup_env.log"
        goto :end_fail
    )
    call :say "      created venv"
)

rem ---------------------------------------------------------------- 3) packages
call :say ""
call :say "[3/5] Installing PySide6 Essentials (first time: 1 - 2 minutes, about 90 MB) ..."
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
"%VPY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 goto :pip_fail
call :say "      packages OK"

rem ---------------------------------------------------------------- 4) self test
call :say ""
call :say "[4/5] Self test (imports, builds the window offscreen, looks for mayapy) ..."
set "ST=%TEMP%\jun_a00560_selftest.txt"
"%VPY%" "app\selftest.py" > "%ST%" 2>> "%LOG%"
set "STRC=%ERRORLEVEL%"
type "%ST%"
type "%ST%" >> "%LOG%"
if not "%STRC%"=="0" (
    call :say "[ERROR] Self test failed - see the message above and setup_env.log"
    goto :end_fail
)

call :say ""
call :say "[5/5] Done."
call :say "============================================================"
call :say " SETUP OK"
rem no ">" inside :say strings - echo would treat it as a redirect and create a file
call :say " Next: double-click Run_JaliBatch.bat (then File menu: Add to Start Menu inside the tool)"
call :say "============================================================"
if "%NOPAUSE%"=="0" pause
exit /b 0

rem ============================================================================
:pip_fail
call :say "[ERROR] Package installation failed. Last lines of setup_env.log:"
powershell -NoProfile -Command "Get-Content -Tail 15 -LiteralPath '%LOG%'"
findstr /i /c:"No matching distribution" "%LOG%" >nul && call :say "  - Hint: no PySide6 wheel for this Python version yet. Run with --force and answer Y to the private Python 3.11 download, or install Python 3.12 / 3.13 / 3.14."
findstr /i /c:"No such file or directory" /c:"path too long" "%LOG%" >nul && call :say "  - Hint: Windows 260-character path limit. The environment folder %VENV% is too deep - set JUN_JALIBATCH_HOME to a short folder (e.g. C:\JUN) and run again."
findstr /i /c:"SSL" /c:"timed out" /c:"ProxyError" "%LOG%" >nul && call :say "  - Hint: network / proxy problem. Check the internet connection or set a pip proxy."
goto :end_fail

:end_fail
call :say ""
call :say "SETUP FAILED - full log: %LOG%"
if "%NOPAUSE%"=="0" pause
exit /b 1

rem ---------------------------------------------------------------------------
:find_python
rem py launcher, newest first. Exit codes are not trusted - see the header.
for %%V in (3.14 3.13 3.12 3.11 3.10) do (
    if not defined PY call :try_cmd "py -%%V"
)
if defined PY exit /b 0
rem python on PATH - skip the Microsoft Store shortcut (WindowsApps)
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PY call :try_path "%%P"
)
if defined PY exit /b 0
rem the private copy downloaded by an earlier run
if exist "%PRIV_PY%" call :try_path "%PRIV_PY%"
if defined PY exit /b 0
rem nothing usable - note what IS installed for the message (e.g. 32-bit or 3.9)
call :probe "py"
if defined P_VER call :note_other "%P_VER%"
exit /b 0

:try_cmd
call :probe "%~1"
if defined P_OK (
    set "PY=%~1"
    set "PYVER=%P_VER%"
) else if defined P_VER (
    call :note_other "%P_VER%"
)
exit /b 0

:try_path
echo %~1 | find /i "WindowsApps" >nul
if not errorlevel 1 exit /b 0
call :probe "%~1"
if defined P_OK (
    set "PY="%~1""
    set "PYVER=%P_VER%"
) else if defined P_VER (
    call :note_other "%P_VER%"
)
exit /b 0

:note_other
echo "%OTHERS%" | find "%~1" >nul
if errorlevel 1 set "OTHERS=%OTHERS% Found Python %~1 (not usable: needs 3.10+ 64-bit)."
exit /b 0

:probe
rem Runs the interpreter and reads what it prints. Sets P_VER (e.g. 3.14) and P_OK (3.10 or newer, 64-bit).
rem  %~1 = "py -3.14" (command) or a full path to python.exe
set "P_OK="
set "P_VER="
set "P_LINE="
if exist "%~1" (
    "%~1" -c "import sys; print('JUNPY', *sys.version_info[:2], 64 if sys.maxsize > 2**32 else 32)" > "%PROBE%" 2>nul
) else (
    call %~1 -c "import sys; print('JUNPY', *sys.version_info[:2], 64 if sys.maxsize > 2**32 else 32)" > "%PROBE%" 2>nul
)
if exist "%PROBE%" set /p P_LINE=<"%PROBE%"
del "%PROBE%" >nul 2>&1
if not defined P_LINE exit /b 0
for /f "tokens=1-4" %%a in ("%P_LINE%") do (
    if "%%a"=="JUNPY" (
        set "P_VER=%%b.%%c"
        if "%%b"=="3" if "%%d"=="64" if %%c GEQ 10 set "P_OK=1"
    )
)
exit /b 0

:download_python
rem python.org NuGet package (a full Python 3.11.9 without an installer) -> %PRIV%
call :say "      downloading Python 3.11.9 (python.org NuGet package) ..."
if exist "%PRIV%" rmdir /s /q "%PRIV%"
if exist "%PRIV_DL%" rmdir /s /q "%PRIV_DL%"
mkdir "%PRIV_DL%"
rem path / url / hash go through environment variables (spaces or quotes in the path cannot break the PowerShell command)
set "JUN_DL=%PRIV_DL%"
set "JUN_DST=%PRIV%"
set "JUN_URL=%PY_URL%"
set "JUN_SHA=%PY_SHA%"
rem Extract tools\* -> %PRIV% but SKIP tools\Lib\site-packages\ (deepest paths, not needed - venv brings pip from Lib\ensurepip).
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$zip=Join-Path $env:JUN_DL 'python.zip'; $dst=$env:JUN_DST;" ^
  "(New-Object Net.WebClient).DownloadFile($env:JUN_URL, $zip);" ^
  "$s=[IO.File]::OpenRead($zip); $h=-join ([Security.Cryptography.SHA256]::Create().ComputeHash($s) | ForEach-Object { $_.ToString('x2') }); $s.Close();" ^
  "if ($h -ne $env:JUN_SHA) { throw ('SHA-256 mismatch: ' + $h) };" ^
  "Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
  "$za=[IO.Compression.ZipFile]::OpenRead($zip); $n=0;" ^
  "foreach ($e in $za.Entries) { $f=$e.FullName; if ($e.Name -and $f.StartsWith('tools/') -and -not $f.StartsWith('tools/Lib/site-packages/')) {" ^
  "  $out=Join-Path $dst ($f.Substring(6).Replace('/', '\')); [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($out)) | Out-Null;" ^
  "  [IO.Compression.ZipFileExtensions]::ExtractToFile($e, $out, $true); $n++ } };" ^
  "$za.Dispose(); Write-Output ('download + SHA-256 + extract OK: ' + $n + ' files')" >> "%LOG%" 2>&1
if errorlevel 1 (
    call :say "[ERROR] Download / extract failed - see setup_env.log"
    call :say "        Network or proxy problem (check the internet connection or the proxy)."
    exit /b 1
)
rmdir /s /q "%PRIV_DL%"
if not exist "%PRIV_PY%" (
    call :say "[ERROR] The downloaded package has no python.exe - see setup_env.log"
    exit /b 1
)
call :say "      private Python 3.11.9 is in %PRIV%"
exit /b 0

:say
echo(%~1
>> "%LOG%" echo(%~1
exit /b 0
