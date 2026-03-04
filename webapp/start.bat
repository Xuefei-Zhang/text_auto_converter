@echo off
setlocal

REM Get the directory where this batch file is located (works from any location)
set "WEBAPP_DIR=%~dp0"

echo ============================================================
echo Sensor Configuration Converter Web App
echo ============================================================
echo.
echo Webapp Directory: %WEBAPP_DIR%
echo.

REM Change to the webapp directory
cd /d "%WEBAPP_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.x from https://python.org
    pause
    exit /b 1
)

REM Check if Flask is installed, if not install dependencies
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies
        echo Please run: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo.
echo Starting server...
echo.
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

REM Start the Flask application
python app.py

pause
