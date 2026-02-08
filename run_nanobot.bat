@echo off
echo ========================================================
echo Starting Nanobot Gateway...
echo ========================================================
python -m nanobot gateway
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Nanobot stopped with an error.
    pause
)
