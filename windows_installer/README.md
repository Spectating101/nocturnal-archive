# Cite Agent Windows Installer Builder

This directory contains everything needed to build a Windows installer for Cite Agent.

## 🎯 What You Get

A single `.exe` installer that:
- ✅ Bundles Python 3.13 (no Python installation needed)
- ✅ Installs cite-agent v1.3.7 and all dependencies
- ✅ Creates desktop shortcut
- ✅ Auto-updates when user launches (from PyPI)
- ✅ Zero configuration required
- ✅ Self-contained (no conflicts with user's Python)

## 📋 Prerequisites

### Required (on Windows):

1. **Python 3.8+** (to run the build script)
   - Download: https://www.python.org/downloads/

2. **Inno Setup 6** (free installer compiler)
   - Download: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

### Optional (for custom launcher):

3. **MinGW-w64** (to compile launcher.c)
   - Download via MSYS2: https://www.msys2.org/
   - Or use the batch script launcher (no compilation needed)

## 🚀 Quick Start

### Option 1: Build Installer (Recommended)

```bash
cd windows_installer
python build.py
```

This will:
1. Download Python 3.13 embedded (~30MB)
2. Install pip into it
3. Install cite-agent v1.3.7
4. Create launcher script
5. Compile installer with Inno Setup
6. Output: `dist/CiteAgent-Setup-v1.3.7.exe` (~60-80MB)

**Build time:** 3-5 minutes

### Option 2: Build with Custom Launcher

If you want a `.exe` launcher instead of `.bat`:

```bash
# First, compile the launcher
compile_launcher.bat

# Then build the installer (it will detect launcher.exe)
python build.py
```

## 🔐 Code Signing (Optional)

### For Beta Testing (Self-Signed):

```bash
# Create self-signed certificate
create_self_signed_cert.bat

# Sign the installer
sign.bat dist\CiteAgent-Setup-v1.3.7.exe
```

**Note:** Self-signed installers show "Unknown Publisher" warning. Users must click "More info" → "Run anyway" once.

### For Production (Real Certificate):

1. Purchase code signing certificate:
   - DigiCert: ~$200/year
   - Sectigo: ~$150/year

2. Save as `certificate.pfx` in this directory

3. Sign the installer:
   ```bash
   sign.bat dist\CiteAgent-Setup-v1.3.7.exe
   ```

4. Verify:
   ```bash
   signtool verify /pa dist\CiteAgent-Setup-v1.3.7.exe
   ```

## 📦 Distribution Package

Create a distribution folder with:

```
CiteAgent_v1.3.7_Beta/
├── CiteAgent-Setup-v1.3.7.exe          ← Main installer
├── README_FROM_DEVELOPER.txt           ← Your personal letter
├── INSTALL_INSTRUCTIONS.txt            ← Step-by-step guide
└── VERIFY_CHECKSUMS.txt                ← SHA256 hash
```

Generate checksums:

```bash
cd dist
certutil -hashfile CiteAgent-Setup-v1.3.7.exe SHA256 > VERIFY_CHECKSUMS.txt
```

## 🔧 Troubleshooting

### Build fails: "Inno Setup not found"
- Install from: https://jrsoftware.org/isdl.php
- Or update `build.py` line 198 with your Inno Setup path

### Build fails: "Python download failed"
- Check your internet connection
- Or manually download from: https://www.python.org/ftp/python/3.13.1/python-3.13.1-embed-amd64.zip
- Place in `build/` directory

### Installer shows "Unknown Publisher" warning
- Expected for self-signed certificates
- Get a real certificate for production
- Or provide clear instructions to users (see README_FROM_DEVELOPER.txt template)

### cite-agent doesn't launch after install
- Check installation log: `C:\Program Files\CiteAgent\install.log`
- Verify Python: `C:\Program Files\CiteAgent\python\python.exe --version`
- Test manually: Run `CiteAgent.bat` from installation directory

## 📁 File Structure

```
windows_installer/
├── build.py                        ← Main build script
├── launcher.c                      ← C launcher (optional)
├── compile_launcher.bat            ← Compile launcher.c
├── installer.iss                   ← Inno Setup script (auto-generated)
├── icon.ico                        ← App icon (add your own)
├── sign.bat                        ← Code signing script
├── create_self_signed_cert.bat     ← Generate test certificate
├── README.md                       ← This file
│
├── build/                          ← Build artifacts (auto-generated)
│   ├── python-3.13.1.zip          ← Downloaded Python
│   ├── python/                    ← Extracted Python
│   └── CiteAgent/                 ← Ready-to-package app
│       ├── python/                ← Bundled Python + cite-agent
│       └── CiteAgent.bat          ← Launcher script
│
└── dist/                           ← Final installer (auto-generated)
    └── CiteAgent-Setup-v1.3.7.exe ← Distributable installer
```

## 🔄 Auto-Update

The installer creates a self-contained Python environment. When users launch cite-agent:

1. It checks PyPI for updates (once per 24 hours)
2. If new version available → downloads and installs automatically
3. User restarts cite-agent → uses new version

**Users never need to reinstall the entire package.**

## 🧪 Testing

Test the installer on a clean Windows VM:

1. Install Windows 10/11 in VM
2. Do NOT install Python
3. Run `CiteAgent-Setup-v1.3.7.exe`
4. Launch from desktop shortcut
5. Verify cite-agent works correctly

## 💡 Tips

- **Keep it simple:** Users should just double-click the installer
- **Include README_FROM_DEVELOPER.txt:** Builds trust, explains warnings
- **Test on clean machine:** Catches missing dependencies
- **Sign the installer:** Reduces warnings (even self-signed helps)
- **Provide screenshots:** Show "Run anyway" steps if unsigned

## 📞 Support

If users have issues:
1. Check `C:\Program Files\CiteAgent\install.log`
2. Verify Python works: Open Command Prompt, run:
   ```
   "C:\Program Files\CiteAgent\python\python.exe" --version
   ```
3. Test cite-agent manually:
   ```
   cd "C:\Program Files\CiteAgent"
   CiteAgent.bat
   ```

## 🎉 Success Checklist

- [ ] Python 3.8+ installed on build machine
- [ ] Inno Setup 6 installed
- [ ] `python build.py` completes without errors
- [ ] Installer created in `dist/` directory
- [ ] Installer tested on clean Windows VM
- [ ] Desktop shortcut works
- [ ] cite-agent launches and responds to queries
- [ ] Auto-update checked (run on consecutive days)
- [ ] README_FROM_DEVELOPER.txt included in distribution
- [ ] Optional: Installer signed (self-signed or real certificate)

---

**Ready to build?** Just run: `python build.py`

The entire process is automated. Sit back and watch. ☕
