@echo off
setlocal EnableExtensions

echo ===== CODEX BOOTSTRAP START =====

if not defined SystemRoot set "SystemRoot=C:\Windows"
if not defined WINDIR set "WINDIR=%SystemRoot%"
if not defined COMSPEC set "COMSPEC=%SystemRoot%\System32\cmd.exe"

if not defined USERPROFILE (
    if defined TEMP (
        for /f "tokens=1,2,3,* delims=\" %%A in ("%TEMP%") do (
            if /I "%%A\%%B"=="C:\Users" set "USERPROFILE=%%A\%%B\%%C"
        )
    )
)
if not defined USERPROFILE (
    if defined USERNAME (
        set "USERPROFILE=C:\Users\%USERNAME%"
    ) else (
        set "USERPROFILE=C:\Users\32118"
    )
)

if not defined HOMEDRIVE set "HOMEDRIVE=%USERPROFILE:~0,2%"
if not defined HOMEPATH set "HOMEPATH=%USERPROFILE:~2%"
if not defined APPDATA set "APPDATA=%USERPROFILE%\AppData\Roaming"
if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"

if not defined TEMP set "TEMP=%USERPROFILE%\AppData\Local\Temp"
if not defined TMP set "TMP=%USERPROFILE%\AppData\Local\Temp"

if not exist "%TEMP%" 2>nul mkdir "%TEMP%"
if not exist "%TMP%" 2>nul mkdir "%TMP%"
if not exist "%TEMP%" set "TEMP=C:\Windows\Temp"
if not exist "%TMP%" set "TMP=%TEMP%"

set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%SystemRoot%\System32\WindowsPowerShell\v1.0\;%PATH%"
chcp 65001 >nul 2>nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PYTHONUTF8=1
set NO_COLOR=1

echo ===== REPAIRED ENV =====
echo SystemRoot=%SystemRoot%
echo WINDIR=%WINDIR%
echo USERPROFILE=%USERPROFILE%
echo TEMP=%TEMP%
echo TMP=%TMP%
echo PATH_PREFIX=%PATH:~0,120%...
echo PYTHONIOENCODING=%PYTHONIOENCODING%
echo PYTHONLEGACYWINDOWSSTDIO=%PYTHONLEGACYWINDOWSSTDIO%
echo PYTHONUTF8=%PYTHONUTF8%

set "FAIL=0"

echo ===== SMOKE: socket =====
echo [CMD] python -c "import socket; socket.socket(); print('socket_ok')"
echo import socket;socket.socket();print('socket_ok')|python
set "RC=%ERRORLEVEL%"
echo [EXIT_CODE] %RC%
if not "%RC%"=="0" set "FAIL=1"

echo ===== SMOKE: _overlapped =====
echo [CMD] python -c "import _overlapped; print('_overlapped_ok')"
echo import _overlapped;print('_overlapped_ok')|python
set "RC=%ERRORLEVEL%"
echo [EXIT_CODE] %RC%
if not "%RC%"=="0" set "FAIL=1"

echo ===== SMOKE: asyncio =====
echo [CMD] python -c "import asyncio; print('asyncio_ok')"
echo import asyncio;print('asyncio_ok')|python
set "RC=%ERRORLEVEL%"
echo [EXIT_CODE] %RC%
if not "%RC%"=="0" set "FAIL=1"

echo ===== SMOKE: nanobot help =====
echo [CMD] python -m nanobot --help
python -m nanobot --help
set "RC=%ERRORLEVEL%"
echo [EXIT_CODE] %RC%
if not "%RC%"=="0" set "FAIL=1"

if "%FAIL%"=="0" (
    echo BOOTSTRAP_RESULT=PASS
    exit /b 0
) else (
    echo BOOTSTRAP_RESULT=FAIL
    exit /b 1
)
