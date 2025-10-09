#!/bin/bash
# Linux Installer Build Script
# Creates .deb and .rpm packages for Linux distributions

set -e

echo ""
echo "========================================"
echo "  Nocturnal Archive Linux Installer"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Navigate to project root
cd ../..

APP_NAME="nocturnal-archive"
VERSION="1.0.0"
ARCH="amd64"

# Install dependencies
echo "[1/6] Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Build executable
echo ""
echo "[2/6] Building executable with PyInstaller..."
pyinstaller --name nocturnal \
    --onefile \
    --console \
    --add-data "nocturnal_archive:nocturnal_archive" \
    --hidden-import=nocturnal_archive \
    --hidden-import=flask \
    --hidden-import=anthropic \
    nocturnal_archive/cli_enhanced.py

# Create .deb package structure
echo ""
echo "[3/6] Creating .deb package..."
DEB_DIR="installers/linux/deb/${APP_NAME}_${VERSION}_${ARCH}"
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${DEB_DIR}/usr/share/doc/${APP_NAME}"

# Copy executable
cp dist/nocturnal "${DEB_DIR}/usr/bin/"
chmod +x "${DEB_DIR}/usr/bin/nocturnal"

# Create control file
cat > "${DEB_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Nocturnal Research <support@nocturnal.dev>
Description: Research & Finance Terminal Intelligence
 Nocturnal Archive is an AI-powered research and finance terminal
 designed for academic researchers and data analysts.
 .
 Features:
  - Academic paper search and analysis
  - Financial data analysis
  - SEC filings research
  - Beautiful terminal interface
  - Offline mode support
Depends: python3 (>= 3.8)
Homepage: https://nocturnal.dev
EOF

# Create desktop entry
cat > "${DEB_DIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Nocturnal Archive
Comment=Research & Finance Terminal Intelligence
Exec=/usr/bin/nocturnal
Icon=nocturnal-archive
Terminal=true
Categories=Utility;Education;Science;
Keywords=research;finance;terminal;ai;
EOF

# Copy documentation
cp README.md "${DEB_DIR}/usr/share/doc/${APP_NAME}/"

# Build .deb package
dpkg-deb --build "${DEB_DIR}"
mv "${DEB_DIR}.deb" "installers/linux/dist/${APP_NAME}_${VERSION}_${ARCH}.deb"

echo "✅ .deb package created"

# Create .rpm package
echo ""
echo "[4/6] Creating .rpm package..."

# Check if rpmbuild is available
if command -v rpmbuild &> /dev/null; then
    RPM_DIR="$HOME/rpmbuild"
    mkdir -p "${RPM_DIR}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    
    # Create spec file
    cat > "${RPM_DIR}/SPECS/${APP_NAME}.spec" << EOF
Name:           ${APP_NAME}
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Research & Finance Terminal Intelligence
License:        MIT
URL:            https://nocturnal.dev
Source0:        %{name}-%{version}.tar.gz

BuildArch:      x86_64
Requires:       python3 >= 3.8

%description
Nocturnal Archive is an AI-powered research and finance terminal
designed for academic researchers and data analysts.

%install
rm -rf \$RPM_BUILD_ROOT
mkdir -p \$RPM_BUILD_ROOT/usr/bin
mkdir -p \$RPM_BUILD_ROOT/usr/share/applications
cp %{_sourcedir}/nocturnal \$RPM_BUILD_ROOT/usr/bin/
cp %{_sourcedir}/${APP_NAME}.desktop \$RPM_BUILD_ROOT/usr/share/applications/

%files
/usr/bin/nocturnal
/usr/share/applications/${APP_NAME}.desktop

%changelog
* $(date +"%a %b %d %Y") Nocturnal Research <support@nocturnal.dev> - ${VERSION}-1
- Initial release
EOF
    
    # Copy files for RPM build
    cp dist/nocturnal "${RPM_DIR}/SOURCES/"
    cp "${DEB_DIR}/usr/share/applications/${APP_NAME}.desktop" "${RPM_DIR}/SOURCES/"
    
    # Build RPM
    rpmbuild -bb "${RPM_DIR}/SPECS/${APP_NAME}.spec"
    
    # Copy to dist
    cp "${RPM_DIR}/RPMS/x86_64/${APP_NAME}-${VERSION}-1."*.rpm "installers/linux/dist/"
    
    echo "✅ .rpm package created"
else
    echo "⚠️  rpmbuild not found, skipping .rpm package"
    echo "   Install with: sudo apt install rpm (Debian/Ubuntu)"
    echo "              or: sudo dnf install rpm-build (Fedora/RHEL)"
fi

# Create AppImage
echo ""
echo "[5/6] Creating AppImage..."

if command -v appimagetool &> /dev/null; then
    APPDIR="installers/linux/appimage/Nocturnal.AppDir"
    mkdir -p "${APPDIR}"
    
    # Copy files
    cp -r "${DEB_DIR}/usr" "${APPDIR}/"
    
    # Create AppRun
    cat > "${APPDIR}/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/nocturnal" "$@"
EOF
    chmod +x "${APPDIR}/AppRun"
    
    # Build AppImage
    appimagetool "${APPDIR}" "installers/linux/dist/Nocturnal-${VERSION}-${ARCH}.AppImage"
    
    echo "✅ AppImage created"
else
    echo "⚠️  appimagetool not found, skipping AppImage"
    echo "   Download from: https://github.com/AppImage/AppImageKit/releases"
fi

# Create installation script
echo ""
echo "[6/6] Creating quick install script..."

cat > "installers/linux/install.sh" << 'EOF'
#!/bin/bash
# Quick installation script for Nocturnal Archive

set -e

echo ""
echo "🌙 Nocturnal Archive Installer"
echo ""

# Detect distribution
if [ -f /etc/debian_version ]; then
    DISTRO="debian"
    PKG_EXT="deb"
    INSTALL_CMD="sudo dpkg -i"
elif [ -f /etc/redhat-release ]; then
    DISTRO="redhat"
    PKG_EXT="rpm"
    INSTALL_CMD="sudo rpm -i"
else
    echo "⚠️  Unsupported distribution. Using AppImage..."
    DISTRO="appimage"
fi

# Download and install
VERSION="1.0.0"
BASE_URL="https://github.com/nocturnal-research/nocturnal-archive/releases/download/v${VERSION}"

if [ "$DISTRO" = "appimage" ]; then
    echo "Downloading AppImage..."
    wget "${BASE_URL}/Nocturnal-${VERSION}-amd64.AppImage" -O nocturnal.AppImage
    chmod +x nocturnal.AppImage
    sudo mv nocturnal.AppImage /usr/local/bin/nocturnal
else
    echo "Downloading ${PKG_EXT} package..."
    wget "${BASE_URL}/nocturnal-archive_${VERSION}_amd64.${PKG_EXT}"
    echo "Installing..."
    ${INSTALL_CMD} "nocturnal-archive_${VERSION}_amd64.${PKG_EXT}"
    rm "nocturnal-archive_${VERSION}_amd64.${PKG_EXT}"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run: nocturnal"
echo ""
EOF

chmod +x "installers/linux/install.sh"

echo ""
echo "✅ Done!"
echo ""
echo "Packages created in: installers/linux/dist/"
echo "  - ${APP_NAME}_${VERSION}_${ARCH}.deb"
if [ -f "installers/linux/dist/${APP_NAME}-${VERSION}-1."*.rpm ]; then
    echo "  - ${APP_NAME}-${VERSION}-1.*.rpm"
fi
if [ -f "installers/linux/dist/Nocturnal-${VERSION}-${ARCH}.AppImage" ]; then
    echo "  - Nocturnal-${VERSION}-${ARCH}.AppImage"
fi
echo ""
echo "Quick install script: installers/linux/install.sh"
echo ""
