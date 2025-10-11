#!/bin/bash
# Build .deb package for Ubuntu/Debian
set -e

VERSION="1.0.0"
ARCH="amd64"
PACKAGE="cite-agent"
BUILD_DIR="deb_build"

echo "🐧 Building Debian package..."

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/doc/$PACKAGE"

# Copy binary
cp ../../dist/cite-agent "$BUILD_DIR/usr/bin/"
chmod +x "$BUILD_DIR/usr/bin/cite-agent"

# Create control file
cat > "$BUILD_DIR/DEBIAN/control" << CTRL
Package: $PACKAGE
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Cite-Agent Team <contact@citeagent.dev>
Description: Terminal AI assistant for academic research
 Cite-Agent provides AI-powered research assistance with citation verification.
 Features include paper search, citation formatting, and research synthesis.
CTRL

# Create desktop entry
cat > "$BUILD_DIR/usr/share/applications/cite-agent.desktop" << DESKTOP
[Desktop Entry]
Name=Cite Agent
Comment=AI Research Assistant
Exec=cite-agent
Terminal=true
Type=Application
Categories=Education;Science;
DESKTOP

# Create copyright
cat > "$BUILD_DIR/usr/share/doc/$PACKAGE/copyright" << COPYRIGHT
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: cite-agent
Source: https://github.com/Spectating101/cite-agent

Files: *
Copyright: 2024 Cite-Agent Team
License: MIT
COPYRIGHT

# Build package
dpkg-deb --build "$BUILD_DIR" "../../dist/${PACKAGE}_${VERSION}_${ARCH}.deb"

echo "✅ Debian package built: dist/${PACKAGE}_${VERSION}_${ARCH}.deb"
