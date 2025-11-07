@echo off
REM Image Fetcher - Web Interface Launcher (Windows)

echo ============================================================
echo Image Fetcher - Web Interface
echo ============================================================
echo.
echo Features:
echo   * Beautiful modern UI with purple gradient design
echo   * Real-time progress tracking with animated bars
echo   * Image gallery with modal viewer
echo   * Download history tracking
echo   * Settings panel for API configuration
echo   * Size presets (4K, FHD, HD, Mobile, etc.)
echo.
echo ============================================================
echo.
echo Starting web server...
echo.
echo Open your browser and navigate to:
echo   http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

python web_app.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start web server
    echo.
    echo Make sure all dependencies are installed:
    echo   pip install -r requirements.txt
    echo.
    pause
)
