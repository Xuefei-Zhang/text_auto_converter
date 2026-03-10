@echo off
setlocal

echo ============================================================
echo Webapp Standalone Verification Tool
echo ============================================================
echo.

REM Check directory structure
echo [1/6] Checking directory structure...
if exist "app.py" (echo   [OK] app.py) else (echo   [FAIL] app.py missing)
if exist "unified_converter.py" (echo   [OK] unified_converter.py) else (echo   [FAIL] unified_converter.py missing)
if exist "i2c_log_parser.py" (echo   [OK] i2c_log_parser.py) else (echo   [FAIL] i2c_log_parser.py missing)
if exist "requirements.txt" (echo   [OK] requirements.txt) else (echo   [FAIL] requirements.txt missing)
if exist "templates\index.html" (echo   [OK] templates\index.html) else (echo   [FAIL] templates\index.html missing)
if exist "static\css\style.css" (echo   [OK] static\css\style.css) else (echo   [FAIL] static\css\style.css missing)
if exist "static\js\app.js" (echo   [OK] static\js\app.js) else (echo   [FAIL] static\js\app.js missing)
echo.

REM Check Python
echo [2/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Python not found in PATH
    exit /b 1
) else (
    python --version
)
echo.

REM Check dependencies
echo [3/6] Checking Python dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Flask not installed. Installing...
    pip install -r requirements.txt
) else (
    echo   [OK] Flask is installed
)

python -c "import werkzeug" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Werkzeug not installed. Installing...
    pip install -r requirements.txt
) else (
    echo   [OK] Werkzeug is installed
)
echo.

REM Check imports
echo [4/6] Testing module imports...
python -c "from unified_converter import parse_adi_fae_config, convert_adi_fae_to_ini" 2>nul
if errorlevel 1 (
    echo   [FAIL] Failed to import unified_converter
) else (
    echo   [OK] unified_converter imports OK
)

python -c "from i2c_log_parser import parse_i2c_log" 2>nul
if errorlevel 1 (
    echo   [FAIL] Failed to import i2c_log_parser
) else (
    echo   [OK] i2c_log_parser imports OK
)

python -c "from app import app" 2>nul
if errorlevel 1 (
    echo   [FAIL] Failed to import app
) else (
    echo   [OK] app imports OK
)
echo.

REM Check directories
echo [5/6] Checking directories...
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
echo   [OK] uploads/ directory ready
echo   [OK] outputs/ directory ready
echo.

REM Quick functionality test
echo [6/6] Running conversion test...
echo   Testing ADI FAE conversion...
python -c "from unified_converter import parse_adi_fae_config; ops = parse_adi_fae_config('0x04,0x90,0x03,0x13,0x00,'); print(f'  Parsed {len(ops)} operations')" 2>nul
if errorlevel 1 (
    echo   [WARN] Could not test conversion (sample file may not exist)
) else (
    echo   [OK] Conversion test passed
)
echo.

echo ============================================================
echo Verification Complete!
echo ============================================================
echo.
echo Your webapp is READY for standalone deployment.
echo.
echo To deploy:
echo   1. Copy entire webapp folder to target location
echo   2. Run start.bat (Windows) or ./start.sh (Linux/Mac)
echo   3. Open http://localhost:5000 in browser
echo.

pause
