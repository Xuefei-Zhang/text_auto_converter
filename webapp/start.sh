#!/bin/bash

WEBAPP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "============================================================"
echo "Sensor Configuration Converter Web App"
echo "============================================================"
echo
echo "Webapp Directory: $WEBAPP_DIR"
echo

cd "$WEBAPP_DIR" || exit 1

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.x"
    exit 1
fi

if ! python3 -c "import flask" &> /dev/null; then
    echo
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo
        echo "ERROR: Failed to install dependencies"
        echo "Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo
echo "Starting server..."
echo
echo "Open your browser to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo

python3 app.py
