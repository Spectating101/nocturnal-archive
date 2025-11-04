# Cite-Agent Installation Guide

**Version:** 1.4.0
**Platform:** Windows 10/11 (64-bit)
**Requirements:** None - installer handles everything automatically

---

## 🚀 Quick Install (Recommended)

### Method 1: One-Line Web Installer (Easiest)

Open **PowerShell** and paste this command:

```powershell
iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
```

**Alternative syntax:**
```powershell
irm https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
```

**What it does:**
- ✅ Detects or installs Python 3.11 (no admin rights needed)
- ✅ Creates isolated environment at `%LOCALAPPDATA%\Cite-Agent`
- ✅ Installs cite-agent from PyPI
- ✅ Creates desktop + start menu shortcuts
- ✅ Adds `cite-agent` command to PATH
- ✅ Works without admin rights

**Installation time:** ~2 minutes

---

### Method 2: GUI Installer (Traditional)

1. **Download installer:**
   - [Cite-Agent-Installer-v2.1.exe](https://github.com/Spectating101/cite-agent/releases/latest) (Per-User - Recommended)
   - Or [Cite-Agent-Installer-v2.1-Admin.exe](https://github.com/Spectating101/cite-agent/releases/latest) (Requires admin)

2. **Run installer:**
   - Double-click the `.exe` file
   - Click "Next → Next → Install"
   - Wait ~2 minutes
   - Done!

3. **Launch Cite-Agent:**
   - Desktop icon: Double-click "Cite-Agent"
   - Start Menu: Search "Cite-Agent"
   - Terminal: Type `cite-agent`

---

### Method 3: pip (For Python Users)

If you already have Python 3.9+ installed:

```bash
pip install cite-agent
```

Then run:
```bash
cite-agent
```

---

## 🎯 Usage Examples

### Basic Commands

```bash
# Start interactive session
cite-agent

# Search research papers
cite-agent "machine learning transformers"

# Get stock data
cite-agent "What's the latest on AAPL stock?"

# Show version
cite-agent --version
```

### R Studio / Stata Integration

1. Open R Studio or Stata
2. Find the **Terminal** pane (usually at bottom)
3. Type:
   ```bash
   cite-agent
   ```
4. You now have AI assistance directly in your data analysis environment!

**Important:** If you installed Cite-Agent while R Studio was open, restart R Studio first.

---

## 📁 Installation Locations

### Per-User Installer (Recommended)
- **Install directory:** `%LOCALAPPDATA%\Cite-Agent`
  - Example: `C:\Users\YourName\AppData\Local\Cite-Agent`
- **Python (if installed):** `%LOCALAPPDATA%\Cite-Agent\python`
- **Virtual environment:** `%LOCALAPPDATA%\Cite-Agent\venv`
- **Logs:** `%LOCALAPPDATA%\Cite-Agent\logs\install.log`

### Admin Installer
- **Install directory:** `C:\Program Files\Cite-Agent`
- **Logs:** `%ProgramData%\Cite-Agent\install.log`

---

## 🔧 Troubleshooting

### "cite-agent: command not found"

**Solution 1:** Restart your terminal/PowerShell window

**Solution 2:** Restart your computer (PATH changes need refresh)

**Solution 3:** Use full path temporarily:
```powershell
& "$env:LOCALAPPDATA\Cite-Agent\venv\Scripts\python.exe" -m cite_agent.cli
```

### "Execution policy error" (Web installer)

If you see "running scripts is disabled on this system":

```powershell
# Run installer with bypass flag
powershell -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex"
```

### Python detection issues

The installer automatically handles Python. If you have issues:

1. **Check log file:**
   ```powershell
   notepad "$env:LOCALAPPDATA\Cite-Agent\logs\install.log"
   ```

2. **Manual Python check:**
   ```powershell
   py -3.11 --version
   # or
   python --version
   ```

3. **Force reinstall:**
   - Delete `%LOCALAPPDATA%\Cite-Agent`
   - Run installer again

### Installation fails with network error

**Cause:** Firewall or proxy blocking Python download

**Solutions:**
1. Download Python manually from [python.org](https://www.python.org/downloads/)
2. Install Python 3.11 first
3. Re-run Cite-Agent installer (it will detect existing Python)

### "SmartScreen prevented an unrecognized app" (GUI installer)

**Cause:** Windows SmartScreen warning (installer is not code-signed)

**Solution:**
1. Click "More info"
2. Click "Run anyway"

**Why it happens:** Code signing certificates cost $400/year. The software is safe (inspect source code on GitHub).

---

## 🗑️ Uninstall

### Per-User Installation

**Option 1:** Windows Settings
1. Settings → Apps → Apps & features
2. Search "Cite-Agent"
3. Click "Uninstall"

**Option 2:** Manual removal
```powershell
# Remove installation directory
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Cite-Agent"

# Remove shortcuts
Remove-Item "$env:USERPROFILE\Desktop\Cite-Agent.lnk"
Remove-Item -Recurse "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Cite-Agent"

# Remove from PATH (optional)
# Settings → System → About → Advanced system settings → Environment Variables
# Edit "Path" and remove the Cite-Agent entry
```

**Option 3:** Automated uninstall script
```powershell
iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/uninstall.ps1 | iex
```

### pip Installation

```bash
pip uninstall cite-agent
```

---

## 🌍 Language Support

Cite-Agent supports:
- 🇺🇸 English
- 🇨🇳 Chinese (繁體中文 / 简体中文)
- Auto-detection based on system locale

**Force language:**
```bash
cite-agent --lang en   # English
cite-agent --lang zh   # Chinese
```

---

## 🆘 Getting Help

### Log Files

Always check logs first when troubleshooting:
```powershell
# View installation log
notepad "$env:LOCALAPPDATA\Cite-Agent\logs\install.log"

# View runtime logs (if available)
notepad "$env:LOCALAPPDATA\Cite-Agent\logs\cite-agent.log"
```

### Report Issues

**Before reporting:**
1. Check the [FAQ](https://github.com/Spectating101/cite-agent#faq)
2. Search [existing issues](https://github.com/Spectating101/cite-agent/issues)
3. Collect log files

**Report new issue:**
1. Go to: https://github.com/Spectating101/cite-agent/issues
2. Click "New Issue"
3. Include:
   - Windows version (`winver`)
   - Python version (if known)
   - Full error message
   - Installation log file content

---

## 📋 System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10 (1809+) or Windows 11 |
| **Architecture** | 64-bit (x64) |
| **RAM** | 4 GB minimum, 8 GB recommended |
| **Disk Space** | 500 MB (includes Python if installed) |
| **Internet** | Required for installation & usage |
| **Python** | Auto-installed if not present (3.11.9) |

---

## 🔐 Privacy & Security

- **No telemetry:** Cite-Agent does not collect usage data
- **Local-first:** API keys stored locally using Windows Credential Manager
- **Open source:** Full source code available on GitHub
- **No admin rights:** Per-user installer runs in user space

**API Keys Required:**
- Groq API (free tier available)
- OpenAI API (for Cerebras inference)
- Optional: Semantic Scholar API

All API keys are stored securely in Windows Credential Manager.

---

## 🚀 Advanced Installation

### Custom installation directory

**Web installer:**
```powershell
# Edit install.ps1 before running
$INSTALL_ROOT = "D:\Tools\Cite-Agent"
```

**GUI installer:**
- Use per-user installer
- Installation path: `%LOCALAPPDATA%\Cite-Agent` (not customizable)

### Offline installation

1. **Prepare on internet-connected machine:**
   ```powershell
   # Download Python installer
   iwr -OutFile python-3.11.9-amd64.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

   # Download cite-agent wheel
   pip download cite-agent
   ```

2. **Transfer files to offline machine:**
   - `python-3.11.9-amd64.exe`
   - All `.whl` files from download

3. **Install on offline machine:**
   ```powershell
   # Install Python
   .\python-3.11.9-amd64.exe /quiet InstallAllUsers=0

   # Install cite-agent from local wheel
   python -m venv venv
   .\venv\Scripts\activate
   pip install --no-index --find-links . cite-agent
   ```

### Corporate environments (behind proxy)

```powershell
# Set proxy before running installer
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"

# Run installer
iwr -useb -Proxy $env:HTTP_PROXY https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
```

---

## 📝 Version History

- **v1.4.0** (2025-11-04): Added web installer, improved Python detection
- **v1.3.9** (2025-10-31): Temporary API keys, Cerebras migration
- **v1.3.0** (2025-10-21): GUI installer, bilingual support
- **v1.2.0** (2025-09-15): Initial Windows support

See [CHANGELOG.md](CHANGELOG.md) for full history.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

**Quick links:**
- [Source Code](https://github.com/Spectating101/cite-agent)
- [Report Bug](https://github.com/Spectating101/cite-agent/issues)
- [Request Feature](https://github.com/Spectating101/cite-agent/issues)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

**Made with ❤️ for researchers worldwide**
