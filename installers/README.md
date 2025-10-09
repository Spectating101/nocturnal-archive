# Nocturnal Archive - Beta Distribution Guide

## Overview
This directory contains installer build scripts for distributing Nocturnal Archive as a one-click installable application across Windows, macOS, and Linux.

## 📦 Available Installers

### Windows (.exe)
- **File**: `nocturnal-archive-setup-1.0.0.exe`
- **Tool**: Inno Setup
- **Features**:
  - One-click installation to Program Files
  - Desktop shortcut creation
  - Start Menu integration
  - Optional PATH addition
  - Auto-launch after install

### macOS (.dmg)
- **File**: `nocturnal-archive-1.0.0.dmg`
- **Tool**: PyInstaller + hdiutil
- **Features**:
  - Drag-to-Applications installation
  - Code signing (if certificate available)
  - Native .app bundle
  - Dock integration

### Linux (.deb, .rpm, .AppImage)
- **Files**: 
  - `nocturnal-archive_1.0.0_amd64.deb` (Ubuntu/Debian)
  - `nocturnal-archive-1.0.0-1.rpm` (Fedora/RHEL)
  - `Nocturnal-1.0.0-amd64.AppImage` (Universal)
- **Features**:
  - System integration
  - Desktop entry
  - Terminal launcher

## 🛠️ Building Installers

### Quick Build (Current Platform)
```bash
./build_installers.sh
```

### Windows Build
Requirements:
- Python 3.8+
- Inno Setup 6 (https://jrsoftware.org/isdl.php)

```bash
cd installers/windows
./build.bat
```

### macOS Build
Requirements:
- Python 3.8+
- Xcode Command Line Tools

```bash
cd installers/macos
./build_dmg.sh
```

### Linux Build
Requirements:
- Python 3.8+
- dpkg (for .deb)
- rpmbuild (for .rpm, optional)
- appimagetool (for AppImage, optional)

```bash
cd installers/linux
./build_deb.sh
```

## 📋 Build Process

Each build script follows these steps:

1. **Install Dependencies**: Install Python packages from requirements.txt
2. **Create Executable**: Use PyInstaller to bundle application
3. **Create Installer**: Package executable with platform-specific tools
4. **Sign Application**: Code sign (if certificates available)
5. **Output**: Generate installer in `dist/` directory

## 🚀 Distribution Workflow

### 1. Pre-Release Checklist
- [ ] Update version number in:
  - `setup.py`
  - `nocturnal_archive/__init__.py`
  - Installer scripts
- [ ] Run tests: `pytest tests/`
- [ ] Update CHANGELOG.md
- [ ] Update README.md

### 2. Build All Platforms
```bash
# On Windows
cd installers/windows && build.bat

# On macOS
cd installers/macos && ./build_dmg.sh

# On Linux
cd installers/linux && ./build_deb.sh
```

### 3. Test Installers
- [ ] Windows: Install on clean Windows 10/11 VM
- [ ] macOS: Install on macOS 11+ (Big Sur or later)
- [ ] Linux: Test .deb on Ubuntu 20.04+, .rpm on Fedora 35+

### 4. Upload to Distribution
Upload to:
- GitHub Releases
- Website download page
- Email to beta testers

### 5. Update Website
- Add download links
- Update documentation
- Announce release

## 🔐 Code Signing

### Windows
1. Obtain code signing certificate
2. Install certificate in Windows Certificate Store
3. Update `build.bat` with certificate details

### macOS
1. Enroll in Apple Developer Program
2. Create Developer ID certificate
3. Sign with: `codesign --sign "Developer ID Application" Nocturnal.app`

### Linux
No signing required for beta, but consider:
- GPG signature for .deb/.rpm
- SHA256 checksums

## 📊 Beta Distribution Plan

### Phase 1: Internal Testing (Week 1)
- Build all installers
- Test on team machines
- Fix critical bugs

### Phase 2: Closed Beta (Week 2-3)
- Invite 10-15 academic researchers
- Distribute via private download link
- Collect feedback via dashboard analytics

### Phase 3: Open Beta (Week 4+)
- Public download page
- Marketing campaign
- Monitor dashboard for issues

## 🎯 Success Metrics

Track via Developer Dashboard:
- **Installation Rate**: Downloads vs. successful installs
- **Activation Rate**: Installs vs. first query
- **Retention**: Users active after 7/30 days
- **Usage**: Queries per user, token consumption
- **Errors**: Installation failures, runtime crashes

## 📝 Installer Customization

### Change Version
Update in all files:
```bash
# Find all version references
grep -r "1.0.0" installers/

# Update:
# - installers/windows/nocturnal-setup.iss
# - installers/macos/build_dmg.sh
# - installers/linux/build_deb.sh
```

### Change Branding
- Icons: Replace `.ico`, `.icns`, `.png` in respective directories
- Name: Update `MyAppName` in scripts
- Publisher: Update publisher info

### Add Dependencies
Update PyInstaller command in build scripts:
```bash
--hidden-import=new_package \
```

## 🐛 Troubleshooting

### Windows: "Python not found"
- Install Python 3.8+ from python.org
- Check "Add to PATH" during installation

### macOS: "Developer cannot be verified"
- Right-click app → Open → Open anyway
- Or disable Gatekeeper temporarily

### Linux: "Package dependencies not met"
- Install Python 3.8+: `sudo apt install python3.8`
- Install dependencies: `sudo apt install python3-pip`

### PyInstaller: "Module not found"
- Add to `--hidden-import`: `--hidden-import=missing_module`
- Check imports in code

### Inno Setup: "Error compiling script"
- Verify file paths in .iss file
- Check Icon file exists
- Update version numbers

## 📞 Support

For build issues:
- Check build logs in `installers/*/build.log`
- Review PyInstaller warnings
- Test executable manually before packaging

For distribution issues:
- Verify file permissions (executable bit)
- Check file sizes (should be 50-100MB)
- Test on clean VM

## 🔄 Continuous Integration

### GitHub Actions Workflow (Future)
```yaml
name: Build Installers
on: [push, release]
jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - run: installers/windows/build.bat
      
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - run: installers/macos/build_dmg.sh
      
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: installers/linux/build_deb.sh
```

## 📄 License
All installer scripts are MIT licensed, same as Nocturnal Archive.
