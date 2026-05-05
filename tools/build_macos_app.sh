#!/bin/bash

# DM Toolkit macOS App Builder
# This script creates a native macOS .app wrapper for the toolkit.

APP_NAME="DM Toolkit"
CDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/.."
cd "$CDIR"

echo "Creating native macOS Application: ${APP_NAME}.app"

# 1. Create the App bundle using osacompile
# This creates an app that simply runs the run_toolkit.command
osacompile -o "${APP_NAME}.app" -e "do shell script \"cd '$CDIR' && ./run_toolkit.command\""

# 2. Add an icon if it exists (placeholder for now)
if [ -f "tools/app_icon.icns" ]; then
    cp "tools/app_icon.icns" "${APP_NAME}.app/Contents/Resources/applet.icns"
fi

echo "Success! You can now drag '${APP_NAME}.app' to your Applications folder."
