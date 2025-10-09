#!/bin/bash
# macOS Installer Build Script
# Creates a .dmg installer for macOS

set -e

echo ""
echo "========================================"
echo "  Nocturnal Archive macOS Installer"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Navigate to project root
cd ../..

# Install dependencies
echo "[1/5] Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Build executable
echo ""
echo "[2/5] Building executable with PyInstaller..."
pyinstaller --name Nocturnal \
    --onefile \
    --windowed \
    --icon=installers/macos/nocturnal.icns \
    --add-data "nocturnal_archive:nocturnal_archive" \
    --hidden-import=nocturnal_archive \
    --hidden-import=flask \
    --hidden-import=anthropic \
    --osx-bundle-identifier=dev.nocturnal.archive \
    nocturnal_archive/cli_enhanced.py

# Create .app bundle
echo ""
echo "[3/5] Creating .app bundle..."
mkdir -p "dist/Nocturnal.app/Contents/MacOS"
mkdir -p "dist/Nocturnal.app/Contents/Resources"

cp dist/Nocturnal "dist/Nocturnal.app/Contents/MacOS/"
cp installers/macos/nocturnal.icns "dist/Nocturnal.app/Contents/Resources/"

# Create Info.plist
cat > "dist/Nocturnal.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Nocturnal</string>
    <key>CFBundleIconFile</key>
    <string>nocturnal.icns</string>
    <key>CFBundleIdentifier</key>
    <string>dev.nocturnal.archive</string>
    <key>CFBundleName</key>
    <string>Nocturnal Archive</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create DMG
echo ""
echo "[4/5] Creating DMG installer..."
mkdir -p installers/macos/dist
hdiutil create -volname "Nocturnal Archive" \
    -srcfolder dist/Nocturnal.app \
    -ov -format UDZO \
    installers/macos/dist/nocturnal-archive-1.0.0.dmg

# Sign the application (if certificate available)
echo ""
echo "[5/5] Signing application (if certificate available)..."
if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
    codesign --force --deep --sign "Developer ID Application" dist/Nocturnal.app
    echo "✅ Application signed"
else
    echo "⚠️  No signing certificate found (optional for beta)"
fi

echo ""
echo "✅ Done!"
echo ""
echo "Installer created: installers/macos/dist/nocturnal-archive-1.0.0.dmg"
echo ""
