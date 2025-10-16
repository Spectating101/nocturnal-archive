#!/bin/bash
# macOS Installer Build Script for Cite-Agent v1.0.4
# Run this on a macOS machine with Python 3.9+ installed

set -e  # Exit on error

echo "============================================================"
echo "Building Cite-Agent macOS Installer"
echo "============================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Check if PyInstaller is installed
if ! pip3 show pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Create clean build directory
rm -rf build_macos
mkdir -p build_macos
cd build_macos

# Download the package from PyPI
echo ""
echo "Downloading cite-agent from PyPI..."
pip3 download cite-agent==1.0.4 --no-deps

# Extract the package
echo "Extracting package..."
tar -xzf cite_agent-1.0.4.tar.gz
cd cite_agent-1.0.4

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install requests aiohttp python-dotenv pydantic rich keyring

# Create PyInstaller spec file
echo ""
echo "Creating PyInstaller spec..."
cat > cite-agent.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cite_agent/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('cite_agent/*.py', 'cite_agent'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'cite_agent',
        'cite_agent.cli',
        'cite_agent.enhanced_ai_agent',
        'cite_agent.account_client',
        'cite_agent.setup_config',
        'requests',
        'aiohttp',
        'pydantic',
        'rich',
        'keyring',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='cite-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Create macOS app bundle
app = BUNDLE(
    exe,
    name='Cite-Agent.app',
    icon=None,
    bundle_identifier='com.citeagent.app',
    version='1.0.4',
    info_plist={
        'CFBundleName': 'Cite-Agent',
        'CFBundleDisplayName': 'Cite-Agent',
        'CFBundleVersion': '1.0.4',
        'CFBundleShortVersionString': '1.0.4',
        'NSHighResolutionCapable': True,
    },
)
EOF

# Build the executable
echo ""
echo "Building executable (this may take a few minutes)..."
pyinstaller --clean cite-agent.spec

# Create DMG installer
echo ""
echo "Creating DMG installer..."

# Create temporary directory for DMG contents
DMG_DIR="../../dmg_temp"
mkdir -p "$DMG_DIR"

# Copy app bundle
cp -R dist/Cite-Agent.app "$DMG_DIR/"

# Create symlink to Applications folder
ln -s /Applications "$DMG_DIR/Applications"

# Create README
cat > "$DMG_DIR/README.txt" << 'EOF'
Cite-Agent v1.0.4
==================

Installation:
1. Drag "Cite-Agent.app" to the "Applications" folder
2. Open Terminal
3. Run: /Applications/Cite-Agent.app/Contents/MacOS/cite-agent --setup
4. Follow the setup wizard

Usage:
- Command line: /Applications/Cite-Agent.app/Contents/MacOS/cite-agent "your question"
- Or add to PATH: ln -s /Applications/Cite-Agent.app/Contents/MacOS/cite-agent /usr/local/bin/cite-agent

For more info: https://pypi.org/project/cite-agent/
EOF

# Create DMG
cd ../..
mkdir -p installers

if command -v hdiutil &> /dev/null; then
    echo "Creating DMG with hdiutil..."
    hdiutil create -volname "Cite-Agent 1.0.4" \
        -srcfolder dmg_temp \
        -ov \
        -format UDZO \
        installers/cite-agent-macos-1.0.4.dmg

    echo ""
    echo "============================================================"
    echo "SUCCESS! macOS installer created"
    echo "============================================================"
    echo ""
    echo "Location: installers/cite-agent-macos-1.0.4.dmg"
    echo "Size: $(du -h installers/cite-agent-macos-1.0.4.dmg | cut -f1)"
    echo ""
else
    # Fallback: just create a zip
    echo "hdiutil not available, creating ZIP instead..."
    cd dmg_temp
    zip -r ../installers/cite-agent-macos-1.0.4.zip .
    cd ..

    echo ""
    echo "============================================================"
    echo "SUCCESS! macOS installer (ZIP) created"
    echo "============================================================"
    echo ""
    echo "Location: installers/cite-agent-macos-1.0.4.zip"
    echo "Size: $(du -h installers/cite-agent-macos-1.0.4.zip | cut -f1)"
    echo ""
fi

echo "To test:"
echo "  1. Mount the DMG (or extract ZIP)"
echo "  2. Run: ./Cite-Agent.app/Contents/MacOS/cite-agent --version"
echo ""
echo "To distribute:"
echo "  1. Upload to GitHub Releases"
echo "  2. Or host on your own server"
echo ""

# Cleanup
rm -rf build_macos dmg_temp

echo "Done!"
