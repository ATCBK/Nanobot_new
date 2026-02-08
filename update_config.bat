@echo off
echo ========================================================
echo Updating Nanobot Configuration...
echo ========================================================
python setup_nanobot.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Configuration update failed.
    pause
) else (
    echo.
    echo [SUCCESS] Configuration updated!
    echo You can now run 'run_nanobot.bat' to start the gateway.
    pause
)
