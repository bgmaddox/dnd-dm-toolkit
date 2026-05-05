#!/bin/bash

# DM Toolkit macOS Launcher
# This script automates environment setup and starts the toolkit.

# Get the directory where the script is located
CDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$CDIR"

echo "------------------------------------------"
echo "   DM Toolkit: Portable Launcher (macOS)  "
echo "------------------------------------------"

# 1. Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please download and install Python from: https://www.python.org/downloads/"
    open https://www.python.org/downloads/
    read -p "Press enter to exit..."
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate and Install Requirements
source .venv/bin/activate
echo "Checking dependencies..."
pip install --quiet -r requirements.txt

# 4. Start Server
echo "Starting toolkit..."

# PORTABLE=1 enables dynamic port selection, browser auto-open, and setup wizard
export PORTABLE=1
python3 server.py
