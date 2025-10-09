#!/bin/bash
# Master Build Script - Builds installers for all platforms

set -e

echo ""
echo "========================================"
echo "  Nocturnal Archive - Master Build"
echo "========================================"
echo ""

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
else
    echo "Unknown platform: $OSTYPE"
    exit 1
fi

echo "Detected platform: $PLATFORM"
echo ""

# Create dist directories
mkdir -p installers/windows/dist
mkdir -p installers/macos/dist
mkdir -p installers/linux/dist

# Build based on platform
case $PLATFORM in
    linux)
        echo "Building Linux packages..."
        cd installers/linux
        ./build_deb.sh
        ;;
    macos)
        echo "Building macOS package..."
        cd installers/macos
        ./build_dmg.sh
        ;;
    windows)
        echo "Building Windows installer..."
        cd installers/windows
        ./build.bat
        ;;
esac

echo ""
echo "✅ Build complete!"
echo ""
echo "Installers available in:"
echo "  - installers/windows/dist/"
echo "  - installers/macos/dist/"
echo "  - installers/linux/dist/"
echo ""
