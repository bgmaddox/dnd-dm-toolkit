#!/bin/bash

# build_macos_app.sh
# Creates a native macOS .app wrapper for the DM Toolkit.

APP_NAME="DM Toolkit"
ICON_PATH="tools/DnDIcon-Computer.png"
LAUNCHER="run_toolkit.command"

echo "Building $APP_NAME.app..."

# 1. Create Folder Structure
mkdir -p "$APP_NAME.app/Contents/MacOS"
mkdir -p "$APP_NAME.app/Contents/Resources"

# 2. Create the executable stub
# This stub finds the project root relative to the .app location and runs the launcher.
cat <<EOF > "$APP_NAME.app/Contents/MacOS/launcher"
#!/bin/bash
# Find the directory where the .app bundle is located
APP_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )/../../.." >/dev/null 2>&1 && pwd )"
cd "\$APP_DIR"
./$LAUNCHER
EOF

chmod +x "$APP_NAME.app/Contents/MacOS/launcher"

# 3. Create Info.plist
cat <<EOF > "$APP_NAME.app/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.bgmaddox.dndtoolkit</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
</dict>
</plist>
EOF

# 4. Handle Icon (Attempt conversion to .icns if possible, otherwise just copy)
# Note: Real .icns requires iconutil. For now, we'll just copy the PNG.
# To properly show an icon, the user usually needs a .icns file.
if [ -f "$ICON_PATH" ]; then
    cp "$ICON_PATH" "$APP_NAME.app/Contents/Resources/AppIcon.png"
    echo "Note: Icon copied. For a true dock icon, conversion to .icns is recommended."
fi

echo "Done! You can now move '$APP_NAME.app' to your Applications folder or use it in-place."
echo "Note: The .app must remain in the same folder as '$LAUNCHER' to work."
