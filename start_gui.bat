@echo off
REM Image Fetcher - Desktop GUI Launcher (Windows)

echo ============================================================
echo Image Fetcher - Desktop GUI
echo ============================================================
echo.
echo Launching desktop application...
echo.

python gui_app.py

if errorlevel 1 (
    echo.
    echo Error: Failed to launch GUI application
    echo.
    echo Make sure Python is installed and dependencies are up to date:
    echo   pip install -r requirements.txt
    echo.
    pause
)
