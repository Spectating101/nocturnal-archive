# Cite-Agent Windows Installer - Distribution Guide

**Target Audience:** Developers, release managers, beta testers

This guide explains the **complete distribution solution** for Cite-Agent on Windows.

---

## 🎯 Distribution Strategy Overview

Cite-Agent provides **THREE** installation methods for maximum user reach:

| Method | Best For | File Size | Requires Admin | Internet |
|--------|----------|-----------|----------------|----------|
| **Web Installer** | Power users, developers, CLI enthusiasts | 25 KB script | ❌ No | ✅ Required |
| **GUI Installer** | General users, academics, non-technical | 15-20 KB .exe | ❌ No (per-user) | ✅ Required |
| **pip** | Python developers | N/A | ❌ No | ✅ Required |

---

## 1️⃣ Web Installer (One-Line Command)

### What It Is

A PowerShell script (`install.ps1`) users can run directly from the web:

```powershell
iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
```

### How It Works

1. User pastes command into PowerShell
2. Script downloads from GitHub
3. Detects or installs Python 3.11
4. Creates virtual environment
5. Installs cite-agent from PyPI
6. Creates shortcuts + adds to PATH

### Advantages

- ✅ **Zero files to distribute** - users just copy/paste command
- ✅ **Always latest version** - pulls from main branch
- ✅ **Easy to update** - just push to GitHub
- ✅ **No compilation needed** - works cross-platform (Linux on GitHub Actions)
- ✅ **Transparent** - users can inspect script source first

### Disadvantages

- ❌ Requires internet during installation
- ❌ Some users don't trust "pipe to interpreter" pattern
- ❌ Execution policy may block on locked-down systems

### Usage Instructions

**Share this with users:**

> **Instant Install (Windows):**
>
> 1. Press `Win + X` → Select "Windows PowerShell" or "Terminal"
> 2. Paste this command:
>    ```powershell
>    iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
>    ```
> 3. Press Enter and wait ~2 minutes
> 4. Done! Type `cite-agent` to start

### Distribution

**GitHub README.md:**
```markdown
## Quick Install (Windows)

```powershell
iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
```
```

**Social media / Email:**
```
Install Cite-Agent in 10 seconds:
iwr -useb https://cutt.ly/cite-agent | iex

(Windows - requires PowerShell)
```

**QR Code:**
Generate QR code pointing to:
```
https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1
```

---

## 2️⃣ GUI Installer (.exe Files)

### What It Is

Professional Windows installer built with **Inno Setup**:
- `Cite-Agent-Installer-v2.1.exe` (Per-user - recommended)
- `Cite-Agent-Installer-v2.1-Admin.exe` (System-wide - requires admin)

### How It Works

1. User downloads `.exe` file
2. Double-clicks to launch wizard
3. Clicks "Next → Next → Install"
4. Inno Setup extracts PowerShell script
5. PowerShell script installs Python + cite-agent
6. Desktop/Start Menu shortcuts created

### Advantages

- ✅ **Familiar UX** - traditional Windows installer experience
- ✅ **Professional appearance** - proper wizard, progress bars, icons
- ✅ **Uninstall support** - appears in Windows Settings → Apps
- ✅ **Bilingual** - English/Chinese support in UI
- ✅ **Trusted pattern** - users comfortable with .exe installers

### Disadvantages

- ❌ **Requires Windows to build** - cannot compile on Linux/Mac
- ❌ **Manual distribution** - need to upload files somewhere
- ❌ **SmartScreen warnings** - unless code-signed ($400/year)
- ❌ **Version updates** - need to rebuild and redistribute

### Building the Installers

#### Automated (GitHub Actions)

**Trigger automatic build:**

```bash
# Push changes to installer files
git add windows_installer/
git commit -m "Update installer"
git push origin main

# Or manually trigger workflow
# GitHub → Actions → "Build Windows Installers" → Run workflow
```

**Download artifacts:**
1. Go to: https://github.com/Spectating101/cite-agent/actions
2. Find latest "Build Windows Installers" run
3. Download artifacts:
   - `Cite-Agent-Installer-v2.1-PerUser.exe`
   - `Cite-Agent-Installer-v2.1-Admin.exe`

#### Manual (Windows Machine)

**Requirements:**
- Windows 10/11
- Inno Setup 6.x ([download](https://jrsoftware.org/isdl.php))

**Steps:**

```powershell
# Clone repository
git clone https://github.com/Spectating101/cite-agent.git
cd cite-agent/windows_installer

# Compile per-user installer (recommended)
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" cite-agent-installer-peruser.iss

# Compile admin installer
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" cite-agent-installer.iss

# Installers created:
# - Cite-Agent-Installer-v2.1.exe (per-user)
# - Cite-Agent-Installer-v2.1-Admin.exe (system-wide)
```

### Distribution

**GitHub Releases (Recommended):**

1. Create new release:
   ```bash
   git tag v1.4.0
   git push origin v1.4.0
   ```

2. Go to: https://github.com/Spectating101/cite-agent/releases

3. Click "Draft a new release"

4. Upload installers:
   - `Cite-Agent-Installer-v2.1.exe`
   - `Cite-Agent-Installer-v2.1-Admin.exe`

5. GitHub Actions automatically builds and uploads on release

**Direct download link:**
```
https://github.com/Spectating101/cite-agent/releases/latest/download/Cite-Agent-Installer-v2.1.exe
```

**Alternative hosting:**
- Google Drive (with "Anyone with link" permissions)
- Dropbox public links
- AWS S3 / Cloudflare R2
- Self-hosted web server

---

## 3️⃣ pip Installation

### What It Is

Standard Python package installation:

```bash
pip install cite-agent
```

### Advantages

- ✅ **Standard Python workflow** - familiar to developers
- ✅ **Easy updates** - `pip install --upgrade cite-agent`
- ✅ **Virtual environment support** - works with venv, conda
- ✅ **No extra distribution** - already on PyPI

### Disadvantages

- ❌ Requires Python pre-installed
- ❌ Users must know how to use pip
- ❌ No automatic shortcut creation
- ❌ Not beginner-friendly

### Distribution

**For developers:**
```bash
pip install cite-agent
```

**For researchers with Python:**
```bash
# Create isolated environment (recommended)
python -m venv cite-agent-env
cite-agent-env\Scripts\activate
pip install cite-agent
cite-agent
```

---

## 📊 Recommended Distribution Strategy

### For Different Audiences

**Academic researchers (non-technical):**
→ **GUI Installer** (Cite-Agent-Installer-v2.1.exe)
- Put download link in email signature
- Share in faculty newsletters
- Host on university department website

**Graduate students / tech-savvy users:**
→ **Web Installer** (one-line command)
- Share command in Slack/Discord
- Post in research group chat
- Tweet/LinkedIn post

**Python developers:**
→ **pip** (`pip install cite-agent`)
- Mention in README
- List on PyPI
- Include in `requirements.txt` examples

### Launch Announcement Template

**Email / Blog Post:**

```markdown
# Introducing Cite-Agent: AI Research Assistant for Windows

## Install in 10 seconds:

**Option 1: One-Line Install (PowerShell)**
```powershell
iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
```

**Option 2: Traditional Installer**
[Download Cite-Agent-Installer-v2.1.exe](https://github.com/Spectating101/cite-agent/releases/latest)

**Option 3: pip (Python users)**
```bash
pip install cite-agent
```

## Features:
- 🔍 Search 200M+ research papers
- 📊 Real-time financial data
- 🤖 AI-powered research assistant
- 🌍 Bilingual (English/Chinese)

No admin rights required • Free & open source
```

---

## 🔄 Update Process

### Updating Web Installer

1. Edit `install.ps1`
2. Update version number:
   ```powershell
   $CITE_AGENT_VERSION = "1.5.0"
   ```
3. Commit and push:
   ```bash
   git add install.ps1
   git commit -m "Update web installer to v1.5.0"
   git push origin main
   ```
4. **Done!** Users automatically get new version on next install

### Updating GUI Installer

1. Update version in `.iss` files:
   ```iss
   #define MyAppVersion "1.5.0"
   ```

2. Update PowerShell script version:
   ```powershell
   # In Install-CiteAgent.ps1
   param([string]$DefaultVersion = "1.5.0", ...)
   ```

3. Commit changes:
   ```bash
   git add windows_installer/
   git commit -m "Bump installer version to v1.5.0"
   git push origin main
   ```

4. Create GitHub release:
   ```bash
   git tag v1.5.0
   git push origin v1.5.0
   ```

5. GitHub Actions builds automatically

6. Download artifacts and distribute

### Updating pip Package

```bash
# Update version
# In setup.py and cite_agent/__version__.py
version="1.5.0"

# Build and upload to PyPI
python setup.py sdist bdist_wheel
twine upload dist/*
```

Users update with:
```bash
pip install --upgrade cite-agent
```

---

## 🛡️ Security Considerations

### Web Installer Security

**Risks:**
- Script downloads from GitHub (trusted)
- Executes PowerShell code (users should review first)
- Downloads Python from python.org (official source)

**Mitigations:**
1. **Use HTTPS only** - `iwr -useb` enforces TLS
2. **Transparent source** - users can inspect script before running
3. **Checksum verification** - future enhancement
4. **Pin Python version** - avoid supply chain attacks

**Best practice for users:**
```powershell
# Download script first (don't pipe directly)
iwr -OutFile install.ps1 https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1

# Review contents
notepad install.ps1

# Run if satisfied
.\install.ps1
```

### GUI Installer Security

**SmartScreen Warning:**
- Windows shows "unrecognized app" warning
- Users must click "More info" → "Run anyway"

**Solution: Code Signing**

1. **Purchase certificate** ($200-400/year):
   - DigiCert
   - Sectigo
   - SSL.com

2. **Sign installer:**
   ```powershell
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com Cite-Agent-Installer-v2.1.exe
   ```

3. **Distribute signed .exe** - no more warnings

**Without code signing:**
- Document the warning in instructions
- Explain why it appears
- Provide checksum for verification:
  ```powershell
  # Generate SHA256 checksum
  certutil -hashfile Cite-Agent-Installer-v2.1.exe SHA256
  ```

---

## 📋 Checklist: Preparing for Release

### Pre-Release

- [ ] Update version numbers:
  - [ ] `setup.py`
  - [ ] `cite_agent/__version__.py`
  - [ ] `install.ps1`
  - [ ] `cite-agent-installer-peruser.iss`
  - [ ] `cite-agent-installer.iss`
  - [ ] `Install-CiteAgent.ps1`

- [ ] Update documentation:
  - [ ] `CHANGELOG.md`
  - [ ] `README.md`
  - [ ] `INSTALL.md`
  - [ ] `windows_installer/START_HERE.txt`

- [ ] Test installers:
  - [ ] Web installer (fresh Windows VM)
  - [ ] GUI installer per-user (fresh Windows VM)
  - [ ] GUI installer admin (fresh Windows VM)
  - [ ] pip installation

- [ ] Verify functionality:
  - [ ] Desktop shortcut works
  - [ ] Start menu shortcut works
  - [ ] `cite-agent` command in terminal
  - [ ] R Studio terminal integration
  - [ ] Uninstaller works

### Release

- [ ] Create git tag:
  ```bash
  git tag -a v1.4.0 -m "Release v1.4.0"
  git push origin v1.4.0
  ```

- [ ] GitHub Actions builds installers automatically

- [ ] Download artifacts from Actions

- [ ] Create GitHub Release:
  - [ ] Upload per-user installer
  - [ ] Upload admin installer
  - [ ] Add SHA256 checksums
  - [ ] Write release notes

- [ ] Upload to PyPI:
  ```bash
  python setup.py sdist bdist_wheel
  twine upload dist/*
  ```

### Post-Release

- [ ] Update website/documentation with new download links

- [ ] Announce release:
  - [ ] GitHub Discussions
  - [ ] Twitter/X
  - [ ] LinkedIn
  - [ ] Email to beta testers
  - [ ] Research community forums

- [ ] Monitor for issues:
  - [ ] GitHub Issues
  - [ ] Installation logs from users
  - [ ] Error reports

---

## 🐛 Troubleshooting Build Issues

### "Inno Setup not found"

**GitHub Actions:**
```yaml
- name: Install Inno Setup
  run: choco install innosetup --yes
```

**Local Windows:**
Download from: https://jrsoftware.org/isdl.php

### "PowerShell script not found"

Check file paths in `.iss`:
```iss
Source: "Install-CiteAgent.ps1"; DestDir: "{app}"; Flags: ignoreversion
```

Ensure `Install-CiteAgent.ps1` is in `windows_installer/` directory.

### "Installer runs but cite-agent not working"

Check logs:
```powershell
notepad "$env:LOCALAPPDATA\Cite-Agent\logs\install.log"
```

Common issues:
- Python download failed (firewall)
- pip install failed (network)
- PATH not updated (needs restart)

### "Web installer execution policy error"

Users with restricted execution policy:
```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -useb <URL> | iex"
```

---

## 📞 Support

**For users:**
- Installation guide: [INSTALL.md](INSTALL.md)
- Report issues: https://github.com/Spectating101/cite-agent/issues

**For developers:**
- Build instructions: [windows_installer/BUILD_INSTRUCTIONS.md](windows_installer/BUILD_INSTRUCTIONS.md)
- Inno Setup docs: https://jrsoftware.org/ishelp/

---

**Last Updated:** 2025-11-04
**Installer Version:** 2.1
**Cite-Agent Version:** 1.4.0
