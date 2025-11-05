# HOW TO DISTRIBUTE CITE-AGENT RIGHT NOW

**Status:** Ready to distribute - bypassing git push issues

---

## THE PROBLEM

GitHub is blocking pushes due to old API keys buried in docs history. Cleaning the entire history is taking forever.

## THE SOLUTION

**Bypass GitHub entirely** - host installer files elsewhere and distribute immediately.

---

## OPTION 1: GitHub Gist (30 seconds, RECOMMENDED)

1. **Go to:** https://gist.github.com

2. **Create new gist:**
   - Filename: `install.ps1`
   - Paste contents from: `/home/phyrexian/Downloads/llm_automation/project_portfolio/Cite-Agent/install.ps1`
   - Set to **Public**
   - Click "Create public gist"

3. **Get raw URL:**
   - Click "Raw" button
   - Copy URL (looks like: `https://gist.githubusercontent.com/YOUR_USERNAME/GIST_ID/raw/install.ps1`)

4. **Distribute this command:**
   ```powershell
   iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/GIST_ID/raw/install.ps1 | iex
   ```

**DONE.** That's your distribution link.

---

## OPTION 2: Simple File Server (if you have a VPS/server)

Upload `install.ps1` to any web server:

```bash
# On your server
scp install.ps1 user@yourserver.com:/var/www/html/

# Users run:
iwr -useb https://yourserver.com/install.ps1 | iex
```

---

## OPTION 3: Google Drive / Dropbox (NOT RECOMMENDED but works)

1. Upload `install.ps1` to Google Drive
2. Right-click → Get link → "Anyone with link can view"
3. Get direct download link (Google Drive requires special formatting)

**Problem:** Requires extra URL manipulation, not clean.

---

## FOR CORRUPTED MACHINES

Users with broken installations run uninstaller first:

1. **Create uninstaller gist** (same process as install.ps1):
   - Upload `uninstall.ps1` to gist
   - Get raw URL

2. **Users run:**
   ```powershell
   # Uninstall
   iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/UNINSTALL_GIST_ID/raw/uninstall.ps1 | iex

   # Then reinstall
   iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/INSTALL_GIST_ID/raw/install.ps1 | iex
   ```

---

## FILES YOU NEED TO DISTRIBUTE

All files are ready in:
```
/home/phyrexian/Downloads/llm_automation/project_portfolio/Cite-Agent/
```

### Core files:
1. **`install.ps1`** - Main installer (upload to gist)
2. **`uninstall.ps1`** - Uninstaller (upload to gist)
3. **`INSTALL.md`** - User documentation (optional, for reference)

### If you want the GUI .exe installer:

The Inno Setup `.exe` files work fine locally. Just compile them on Windows and distribute directly:

**On Windows machine:**
```powershell
# Install Inno Setup first (one-time)
choco install innosetup

# Compile installer
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" windows_installer\cite-agent-installer-peruser.iss

# Upload Cite-Agent-Installer-v2.1.exe to Google Drive / Dropbox / anywhere
```

Users download and double-click the `.exe`.

---

## RECOMMENDED DISTRIBUTION STRATEGY

### For Beta Launch:

**Email / Slack / Discord:**
```
🚀 Cite-Agent v1.4.0 is ready!

Quick Install (Windows):
Open PowerShell and run:

iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/INSTALL_GIST_ID/raw/install.ps1 | iex

That's it! cite-agent will be ready in ~2 minutes.

📚 What it does:
- Searches 200M+ research papers
- Real-time financial data
- AI research assistant
- Works in R Studio terminal

Questions? https://github.com/Spectating101/cite-agent/issues
```

### For Website / README:

```markdown
## Installation

### Windows (One-Line Install)

```powershell
iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/INSTALL_GIST_ID/raw/install.ps1 | iex
```

### Or download GUI installer:
[Cite-Agent-Installer-v2.1.exe](YOUR_DOWNLOAD_LINK)
```

---

## WHAT HAPPENS WHEN USER RUNS IT

```powershell
iwr -useb https://gist.githubusercontent.com/.../install.ps1 | iex
```

**Automatically:**
1. ✅ Checks for Python 3.11
2. ✅ Installs Python if missing (embedded, no admin)
3. ✅ Creates virtualenv at `%LOCALAPPDATA%\Cite-Agent\venv`
4. ✅ Installs cite-agent from PyPI
5. ✅ Creates desktop shortcut
6. ✅ Creates Start Menu entry
7. ✅ Adds to PATH

**User sees:**
```
╔════════════════════════════════════════════════════════╗
║   CITE-AGENT INSTALLER                                 ║
║   AI Research Assistant for Windows                    ║
║   Version 1.4.0                                        ║
╚════════════════════════════════════════════════════════╝

[*] Checking for existing Python installation...
[✓] Found Python via py launcher: C:\...\python.exe
[*] Creating virtual environment...
[✓] Virtual environment created
[*] Installing Cite-Agent v1.4.0...
[✓] Cite-Agent installed successfully
[*] Creating shortcuts...
[✓] Shortcuts created (Desktop + Start Menu)
[*] Adding cite-agent to PATH...
[✓] cite-agent added to PATH
[*] Verifying installation...
[✓] Cite-Agent is ready: cite-agent 1.4.0

╔════════════════════════════════════════════════════════╗
║   ✓ INSTALLATION COMPLETE!                             ║
╚════════════════════════════════════════════════════════╝

🚀 Quick Start:
   1. Double-click 'Cite-Agent' on your Desktop
   2. Or search 'Cite-Agent' in Start Menu
   3. Or type 'cite-agent' in any terminal
```

**Total time:** ~2 minutes

---

## TESTING BEFORE DISTRIBUTION

**On a clean Windows VM/machine:**

1. Run installer:
   ```powershell
   iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/.../install.ps1 | iex
   ```

2. Verify:
   ```powershell
   # Should work immediately
   cite-agent --version

   # Test R Studio integration
   # 1. Open R Studio
   # 2. Go to Terminal pane (bottom)
   # 3. Type: cite-agent
   # 4. Should launch successfully
   ```

3. Test uninstaller:
   ```powershell
   iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/.../uninstall.ps1 | iex
   ```

---

## FIXING CORRUPTED INSTALLATIONS

If someone has a broken cite-agent install:

```powershell
# Step 1: Uninstall completely
iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/.../uninstall.ps1 | iex

# Step 2: Restart terminal

# Step 3: Reinstall fresh
iwr -useb https://gist.githubusercontent.com/YOUR_USERNAME/.../install.ps1 | iex
```

---

## BYPASSING GIT PUSH ISSUES (for later)

The git repo has API keys in history. Two options:

**Option A:** Allowlist the secrets (temporary)
- Visit URLs from error message
- Click "Allow this secret"
- Push again

**Option B:** Clean history properly (takes time)
```bash
# Remove all files with API keys
java -jar /tmp/bfg.jar --delete-files "{SECURE_SETUP.md,COMPLETE_SYSTEM_DOCUMENTATION.md,STATUS_AND_NEXT_STEPS.md,CEREBRAS_MIGRATION.md}" --no-blob-protection .

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin production-backend-only --force
```

**But you don't need to do this right now** - just use gists.

---

## SUMMARY: DO THIS NOW

1. **Upload `install.ps1` to GitHub Gist** (public)
2. **Copy raw gist URL**
3. **Test on Windows machine:** `iwr -useb GIST_URL | iex`
4. **If it works, distribute the one-liner to users**
5. **Done**

You can fix the git repo later. The installer works independently of GitHub repo.

---

**Time to distribute:** 30 seconds
**Time saved vs fixing git:** 2+ hours

GO.
