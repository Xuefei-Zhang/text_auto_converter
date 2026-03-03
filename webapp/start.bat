@echo off
echo ============================================================
echo Sensor Configuration Converter Web App
echo ============================================================
echo.
echo Starting server...
echo.
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

cd /d "%~dp0"
python app.py

pause
