# Building the GUI Installer as .exe

You now have a **professional GUI installer** with progress bar, modern UI, and real-time logging.

---

## Files Created:

1. **`Install-Cite-Agent-GUI.ps1`** - PowerShell GUI installer (main file)
2. **`Install-Cite-Agent-GUI.bat`** - Batch launcher (double-click to run)
3. **This guide** - How to convert to .exe

---

## Option 1: Use the .bat file (RECOMMENDED)

**No conversion needed!**

Just distribute `Install-Cite-Agent-GUI.bat` + `Install-Cite-Agent-GUI.ps1` together.

Users double-click the `.bat` file and get the full GUI experience.

**Advantages:**
- ✅ No SmartScreen warning (it's just text)
- ✅ No compilation needed
- ✅ Easy to update (just edit the .ps1 file)
- ✅ Users can inspect source code

**Distribution:**
```
Cite-Agent-Installer/
├── Install-Cite-Agent-GUI.bat  (launcher)
└── Install-Cite-Agent-GUI.ps1  (GUI script)
```

Zip these two files and distribute. Users unzip and double-click the `.bat`.

---

## Option 2: Convert to standalone .exe

If you REALLY want a single `.exe` file:

### Step 1: Install ps2exe

On a Windows machine with PowerShell:

```powershell
# Install ps2exe module
Install-Module -Name ps2exe -Scope CurrentUser

# Or if that fails:
Install-Script -Name ps2exe
```

### Step 2: Convert to .exe

```powershell
# Navigate to the installer directory
cd "path\to\Cite-Agent"

# Convert to .exe
Invoke-ps2exe `
    -inputFile "Install-Cite-Agent-GUI.ps1" `
    -outputFile "Cite-Agent-Installer.exe" `
    -noConsole `
    -title "Cite-Agent Installer" `
    -description "Cite-Agent AI Research Assistant Installer" `
    -company "Cite-Agent Team" `
    -product "Cite-Agent" `
    -version "1.4.0" `
    -requireAdmin:$false
```

### Step 3: Test

Double-click `Cite-Agent-Installer.exe` - GUI should launch.

**Result:**
- Single .exe file (~500 KB)
- Professional GUI with progress bar
- Still downloads latest version from web
- **Still triggers SmartScreen** (unsigned)

---

## Option 3: Use IExpress (Built into Windows)

IExpress is a built-in Windows tool that creates self-extracting installers.

### Step 1: Create IExpress Package

1. Press Win + R, type: `iexpress`
2. Click "Next"
3. Select "Extract files and run an installation command"
4. Package title: "Cite-Agent Installer"
5. Add files:
   - `Install-Cite-Agent-GUI.ps1`
   - `Install-Cite-Agent-GUI.bat`
6. Install command: `Install-Cite-Agent-GUI.bat`
7. Save to: `Cite-Agent-Installer.exe`

**Result:**
- Self-extracting .exe
- Extracts files to temp, runs installer, cleans up
- Still triggers SmartScreen

---

## Option 4: Use NSIS (Advanced)

NSIS (Nullsoft Scriptable Install System) can create professional installers.

### Install NSIS:
Download from: https://nsis.sourceforge.io/

### Create installer script:

```nsis
; Cite-Agent NSIS Installer Script

!include "MUI2.nsh"

Name "Cite-Agent"
OutFile "Cite-Agent-Installer.exe"
InstallDir "$LOCALAPPDATA\Cite-Agent-Setup"

!define MUI_ICON "cite-agent-icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath $INSTDIR
    File "Install-Cite-Agent-GUI.ps1"
    File "Install-Cite-Agent-GUI.bat"

    ExecWait 'powershell -ExecutionPolicy Bypass -File "$INSTDIR\Install-Cite-Agent-GUI.ps1"'

    Delete "$INSTDIR\Install-Cite-Agent-GUI.ps1"
    Delete "$INSTDIR\Install-Cite-Agent-GUI.bat"
    RMDir "$INSTDIR"
SectionEnd
```

Compile with: `makensis cite-agent-installer.nsi`

**Result:**
- Professional installer with branding
- Still triggers SmartScreen

---

## SmartScreen Warning: The Reality

**All .exe methods above will trigger Windows SmartScreen:**

```
Windows protected your PC
Microsoft Defender SmartScreen prevented an unrecognized app from starting.
```

**The ONLY ways to avoid this:**

1. **Code signing certificate** ($400/year) + **6-12 months of reputation building**
2. **Don't use .exe** (use .bat instead)

---

## Recommended Approach: Hybrid Distribution

Offer THREE download options:

### 1. Web Installer (for technical users)

```powershell
iwr -useb https://raw.githubusercontent.com/.../install-clean.ps1 | iex
```

**Pros:** Fastest, no files to download, always latest
**Cons:** Requires copy/paste command

---

### 2. GUI Installer .bat + .ps1 (for visual users)

Download: `Cite-Agent-GUI-Installer.zip`
Contents:
- `Install-Cite-Agent-GUI.bat`
- `Install-Cite-Agent-GUI.ps1`

Unzip, double-click `.bat`, get GUI installer.

**Pros:** Visual progress bar, no SmartScreen warning, familiar pattern
**Cons:** Two files in a zip

---

### 3. Single .exe (for maximum simplicity)

Download: `Cite-Agent-Installer.exe`

Double-click, see SmartScreen warning, click "Run anyway", GUI launches.

**Pros:** Single file, looks professional
**Cons:** SmartScreen warning (scary for some users)

---

## What the GUI Installer Looks Like

```
╔════════════════════════════════════════════════════════╗
║  Cite-Agent Installer                                  ║  (Blue header)
║  AI Research Assistant for Windows | AI學術研究助手      ║
╚════════════════════════════════════════════════════════╝

This installer will:
  • Remove any old versions (clean install)
  • Install Python if needed (no admin required)
  • Install Cite-Agent v1.4.0 from PyPI
  • Create desktop and Start Menu shortcuts
  • Add cite-agent to system PATH

Installation takes approximately 2 minutes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░ 65%

Status: Installing Cite-Agent v1.4.0...

┌────────────────────────────────────────────────────┐
│ [12:34:56] Starting Cite-Agent installation...     │
│ [12:34:58] Cleaning up old installations...        │
│ [12:35:02] Found Python: C:\...\python.exe         │
│ [12:35:05] Creating virtual environment...         │
│ [12:35:12] Installing cite-agent from PyPI...      │
│ [12:35:45] Creating shortcuts...                   │
│ [12:35:47] ✓ Installation complete!                │
└────────────────────────────────────────────────────┘

                              [Install]  [Close]
```

---

## Features of the GUI Installer:

✅ **Modern Windows UI** - Uses native Windows Forms
✅ **Real-time progress bar** - Shows 0-100% progress
✅ **Detailed logging** - Scrollable log with timestamps
✅ **Stage-by-stage updates** - Clear status messages
✅ **Error handling** - Shows friendly error messages
✅ **Success confirmation** - Message box when complete
✅ **Professional appearance** - Blue header, clean layout
✅ **Bilingual support** - English/Chinese text

---

## File Size Comparison:

| Method | File Size |
|--------|-----------|
| Web installer (command) | 0 bytes (just a URL) |
| .bat launcher | 1 KB |
| .ps1 GUI script | 15 KB |
| .bat + .ps1 (zipped) | 8 KB |
| ps2exe .exe | 500 KB |
| IExpress .exe | 20 KB |
| Inno Setup .exe | 50 MB (with Python) |

---

## My Recommendation:

**Distribute the GUI .bat + .ps1 combo.**

**Why:**
1. Professional visual installer (progress bar, modern UI)
2. No SmartScreen warning (it's just text files)
3. Easy to update (just edit .ps1 file)
4. Users get familiar "double-click" experience
5. Transparent (users can inspect source)

**How to distribute:**

1. **Create a zip:**
   ```
   Cite-Agent-Installer-v1.4.0.zip
   ├── Install-Cite-Agent-GUI.bat
   └── Install-Cite-Agent-GUI.ps1
   ```

2. **Upload to GitHub Releases:**
   ```
   https://github.com/Spectating101/cite-agent/releases/latest
   ```

3. **Users download, unzip, double-click .bat**

4. **They see professional GUI installer**

---

## Testing the GUI Installer:

On Windows:

1. **Save both files in same folder:**
   - `Install-Cite-Agent-GUI.ps1`
   - `Install-Cite-Agent-GUI.bat`

2. **Double-click the .bat file**

3. **GUI window should open showing:**
   - Blue header with title
   - Description of what it does
   - Progress bar (starts at 0%)
   - Log window (empty initially)
   - Install button

4. **Click Install button**

5. **Watch progress bar fill and log messages scroll**

6. **See success message when done**

---

## Summary:

| Method | Pros | Cons | Recommended? |
|--------|------|------|--------------|
| **Web installer** | Fastest, always latest | Requires terminal | ✅ Yes (primary) |
| **GUI .bat + .ps1** | Visual, no warning | Two files | ✅ Yes (secondary) |
| **ps2exe .exe** | Single file | SmartScreen warning | ⚠️ Maybe |
| **Inno Setup** | Traditional | Complex, SmartScreen | ❌ No |

**Best strategy:** Offer web installer + GUI .bat combo. Let users choose.

---

**Created:** 2025-11-04
**Version:** 1.4.0
**Status:** Production-ready
