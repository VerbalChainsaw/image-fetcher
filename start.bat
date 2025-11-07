@echo off
REM Image Fetcher - Main Launcher (Windows)

:menu
cls
echo ============================================================
echo                     IMAGE FETCHER v2.0
echo ============================================================
echo.
echo Choose how you want to use Image Fetcher:
echo.
echo   1. Web Interface (Recommended - Beautiful modern UI)
echo   2. Desktop GUI (Native Windows application)
echo   3. Command Line (Advanced users)
echo   4. Run Tests
echo   5. Exit
echo.
echo ============================================================
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto web
if "%choice%"=="2" goto gui
if "%choice%"=="3" goto cli
if "%choice%"=="4" goto test
if "%choice%"=="5" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:web
cls
call start_web.bat
goto end

:gui
cls
call start_gui.bat
goto end

:cli
cls
echo ============================================================
echo Command Line Interface
echo ============================================================
echo.
echo Example commands:
echo.
echo   Basic usage:
echo     python image_fetcher.py "sunset beach" 10
echo.
echo   With size preset:
echo     python image_fetcher.py "mountain landscape" 20 --size 4k
echo.
echo   Interactive mode:
echo     python image_fetcher.py --interactive
echo.
echo   Setup API keys:
echo     python image_fetcher.py --setup
echo.
echo ============================================================
echo.
pause
goto menu

:test
cls
echo ============================================================
echo Running Test Suite
echo ============================================================
echo.
python test_suite.py
echo.
echo ============================================================
echo.
pause
goto menu

:end
