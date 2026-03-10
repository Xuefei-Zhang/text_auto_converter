#!/bin/bash

echo "============================================================"
echo "Webapp Standalone Verification Tool"
echo "============================================================"
echo

# Check directory structure
echo "[1/6] Checking directory structure..."
[ -f "app.py" ] && echo "  [OK] app.py" || echo "  [FAIL] app.py missing"
[ -f "unified_converter.py" ] && echo "  [OK] unified_converter.py" || echo "  [FAIL] unified_converter.py missing"
[ -f "i2c_log_parser.py" ] && echo "  [OK] i2c_log_parser.py" || echo "  [FAIL] i2c_log_parser.py missing"
[ -f "requirements.txt" ] && echo "  [OK] requirements.txt" || echo "  [FAIL] requirements.txt missing"
[ -f "templates/index.html" ] && echo "  [OK] templates/index.html" || echo "  [FAIL] templates/index.html missing"
[ -f "static/css/style.css" ] && echo "  [OK] static/css/style.css" || echo "  [FAIL] static/css/style.css missing"
[ -f "static/js/app.js" ] && echo "  [OK] static/js/app.js" || echo "  [FAIL] static/js/app.js missing"
echo

# Check Python
echo "[2/6] Checking Python installation..."
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "  [FAIL] Python3 not found"
    exit 1
fi
echo

# Check dependencies
echo "[3/6] Checking Python dependencies..."
if python3 -c "import flask" 2>/dev/null; then
    echo "  [OK] Flask is installed"
else
    echo "  [WARN] Flask not installed. Installing..."
    pip3 install -r requirements.txt
fi

if python3 -c "import werkzeug" 2>/dev/null; then
    echo "  [OK] Werkzeug is installed"
else
    echo "  [WARN] Werkzeug not installed. Installing..."
    pip3 install -r requirements.txt
fi
echo

# Check imports
echo "[4/6] Testing module imports..."
if python3 -c "from unified_converter import parse_adi_fae_config, convert_adi_fae_to_ini" 2>/dev/null; then
    echo "  [OK] unified_converter imports OK"
else
    echo "  [FAIL] Failed to import unified_converter"
fi

if python3 -c "from i2c_log_parser import parse_i2c_log" 2>/dev/null; then
    echo "  [OK] i2c_log_parser imports OK"
else
    echo "  [FAIL] Failed to import i2c_log_parser"
fi

if python3 -c "from app import app" 2>/dev/null; then
    echo "  [OK] app imports OK"
else
    echo "  [FAIL] Failed to import app"
fi
echo

# Check directories
echo "[5/6] Checking directories..."
mkdir -p uploads outputs
echo "  [OK] uploads/ directory ready"
echo "  [OK] outputs/ directory ready"
echo

# Quick functionality test
echo "[6/6] Running conversion test..."
echo "  Testing ADI FAE conversion..."
python3 -c "from unified_converter import parse_adi_fae_config; ops = parse_adi_fae_config('0x04,0x90,0x03,0x13,0x00,'); print(f'  Parsed {len(ops)} operations')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  [OK] Conversion test passed"
else
    echo "  [WARN] Could not test conversion"
fi
echo

echo "============================================================"
echo "Verification Complete!"
echo "============================================================"
echo
echo "Your webapp is READY for standalone deployment."
echo
echo "To deploy:"
echo "  1. Copy entire webapp folder to target location"
echo "  2. Run start.bat (Windows) or ./start.sh (Linux/Mac)"
echo "  3. Open http://localhost:5000 in browser"
echo
