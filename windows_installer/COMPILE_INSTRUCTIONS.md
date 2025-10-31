# Compiling Cite-Agent Windows Installer
**Target:** Generate `Cite-Agent-Installer-v2.0.exe`
**Platform:** Windows 10/11 with admin rights
**Time:** ~5 minutes

---

## Prerequisites

You need:
- ✅ Windows 10 or 11
- ✅ Administrator access
- ✅ Internet connection (to download Inno Setup)
- ✅ This repository's `windows_installer/` folder

---

## Step 1: Get the Repository Files

### Option A: Git Clone (if you have git)
```cmd
git clone https://github.com/Spectating101/cite-agent.git
cd cite-agent\windows_installer
```

### Option B: Download ZIP
1. Download: https://github.com/Spectating101/cite-agent/archive/refs/heads/production-backend-only.zip
2. Extract to: `C:\cite-agent\`
3. Navigate to: `C:\cite-agent\windows_installer\`

### Option C: Upload from Linux
If you have the files on Linux, zip them:
```bash
cd /home/phyrexian/Downloads/llm_automation/project_portfolio/Cite-Agent
zip -r cite-agent-windows-installer.zip windows_installer/
```
Then transfer to Windows and extract.

---

## Step 2: Install Inno Setup 6.x

### Download
1. Visit: https://jrsoftware.org/isdl.php
2. Click: **Inno Setup 6.3.3** (or latest 6.x version)
3. Download: `innosetup-6.3.3.exe` (~3 MB)

### Install
1. Run `innosetup-6.3.3.exe`
2. Click: **Next → I Agree → Next → Next → Install**
3. Wait 30 seconds
4. Click: **Finish**

**Verify installation:**
- Start Menu → Search "Inno Setup Compiler"
- You should see: "Inno Setup Compiler" icon

---

## Step 3: Open the Installer Script

### Method 1: GUI (Recommended)

1. **Launch Inno Setup Compiler**
   - Start Menu → "Inno Setup Compiler"
   - Or run: `C:\Program Files (x86)\Inno Setup 6\Compil32.exe`

2. **Open the script**
   - File → Open
   - Navigate to: `C:\cite-agent\windows_installer\cite-agent-installer.iss`
   - Click: **Open**

**You should see:**
- Script editor with lines like:
  ```iss
  #define MyAppName "Cite-Agent"
  #define MyAppVersion "1.3.9"
  ```

---

## Step 4: Compile the Installer

### Option 1: GUI Compile (Easiest)

1. **Press F9** (or Build → Compile)
2. **Watch the output:**
   ```
   Compiling...
   Processing: [Setup]
   Processing: [Files]
   Processing: [Icons]
   Processing: [Run]
   Successful compile (0 sec)
   ```

3. **Look for success message:**
   ```
   Compile completed successfully.
   Output: Cite-Agent-Installer-v2.0.exe
   ```

**Time:** 5-10 seconds

### Option 2: Command Line (For automation)

Open **Command Prompt (Admin):**
```cmd
cd C:\cite-agent\windows_installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" cite-agent-installer.iss
```

**Expected output:**
```
Inno Setup 6 Command-Line Compiler
Copyright (C) 1997-2024 Jordan Russell

Compiling cite-agent-installer.iss
- Preprocessor: Processing
- Compiling: Processing setup sections
- Compiling [Setup]
...
Successful compile (0.5 seconds)
```

---

## Step 5: Verify the Output

### Check the file exists

**Location:** `C:\cite-agent\windows_installer\Cite-Agent-Installer-v2.0.exe`

**Right-click → Properties:**
- Size: ~15-20 KB (small because it downloads components)
- Type: Application (.exe)

### Quick sanity check

**DO NOT run the installer yet** (unless you want to test it).

Just verify:
```cmd
dir Cite-Agent-Installer-v2.0.exe
```

**Expected:**
```
10/31/2025  02:45 PM            18,432 Cite-Agent-Installer-v2.0.exe
```

---

## Step 6: Package for Distribution

### Create ZIP for transfer

```cmd
cd C:\cite-agent\windows_installer
tar -a -c -f Cite-Agent-Installer-v2.0.zip Cite-Agent-Installer-v2.0.exe START_HERE.txt README.txt QUICKSTART.txt
```

**Or use File Explorer:**
1. Select: `Cite-Agent-Installer-v2.0.exe`, `START_HERE.txt`, `README.txt`, `QUICKSTART.txt`
2. Right-click → Send to → Compressed (zipped) folder
3. Name: `Cite-Agent-Installer-v2.0.zip`

---

## Step 7 (OPTIONAL): Smoke Test

### Test the installer on the same VM

1. **Double-click:** `Cite-Agent-Installer-v2.0.exe`
2. **You should see:**
   - Welcome screen (bilingual English/Chinese)
   - "Next" button
3. **Click Next → Next → Install**
4. **Wait ~2 minutes** (installs Python + cite-agent)
5. **Verify:**
   - Desktop shortcut: "Cite-Agent" appears
   - Start Menu: "Cite-Agent" entry exists

### Test the desktop shortcut

1. **Double-click:** Desktop "Cite-Agent" icon
2. **Should open:** Terminal with cite-agent running
3. **Type:** `quit` (to exit)

**If smoke test passes:** ✅ Installer works!

---

## Step 8: Transfer Back to Linux

### From Windows to Linux

**Option A: Network transfer**
```cmd
REM On Windows, share the folder
REM On Linux:
scp user@windows-machine:C:/cite-agent/windows_installer/Cite-Agent-Installer-v2.0.zip ~/Downloads/
```

**Option B: Upload to cloud**
- Upload to Google Drive / Dropbox
- Download on Linux

**Option C: USB drive**
- Copy to USB on Windows
- Plug into Linux machine

---

## Troubleshooting

### Error: "Cannot find PowerShell script"

**Cause:** `Install-CiteAgent.ps1` not in same folder as `.iss`

**Fix:**
```cmd
dir Install-CiteAgent.ps1
REM Make sure it exists in windows_installer/
```

### Error: "Failed to compile"

**Check:**
1. Is Inno Setup installed? (`C:\Program Files (x86)\Inno Setup 6\`)
2. Is the `.iss` file in the right folder?
3. Open `.iss` in Notepad - any syntax errors?

### Warning: "Windows protected your PC"

**This is normal** - unsigned .exe triggers SmartScreen.

**For testing:**
- Click: "More info" → "Run anyway"

**For production:**
- Code sign the .exe (requires certificate ~$200/year)

### Installer runs but Python doesn't install

**Cause:** Firewall blocking download

**Fix:**
- Check internet connection
- Temporarily disable firewall
- Or manually install Python 3.11.9 first

---

## Files You Should Have After Compilation

```
windows_installer/
├── cite-agent-installer.iss           (source script)
├── Install-CiteAgent.ps1              (PowerShell installer)
├── cite-agent.bat                     (launcher)
├── START_HERE.txt                     (user instructions)
├── README.txt                         (documentation)
├── QUICKSTART.txt                     (quick guide)
├── CHANGELOG.txt                      (version history)
├── LICENSE.txt                        (license)
└── Cite-Agent-Installer-v2.0.exe     (← GENERATED FILE!)
```

---

## Next Steps After Compilation

1. ✅ **Verify .exe exists** (~18 KB)
2. ✅ **Zip for distribution**
3. ✅ **Smoke test on Windows VM** (optional)
4. ✅ **Transfer to Linux machine**
5. ✅ **Test on clean Windows 11 VM** (final test)
6. ✅ **Distribute to beta testers**

---

## For Beta Testers

Once you have the `.exe`, users just:
1. Download `Cite-Agent-Installer-v2.0.exe`
2. Double-click
3. Click "Next, Next, Install"
4. Wait 2 minutes
5. Done!

Desktop shortcut appears automatically.

---

## Questions?

**If compilation fails:**
- Check Inno Setup version: Help → About (should be 6.x)
- Check all files present: `dir windows_installer\`
- Check script syntax: Open `.iss` in Notepad

**If installer doesn't work:**
- Test on clean Windows VM
- Check Python downloads: https://www.python.org/ftp/python/3.11.9/
- Check logs: `%TEMP%\cite-agent-install.log`

---

**Estimated time:** 5 minutes (if Inno Setup already installed)
**Difficulty:** Easy (just press F9)
**Result:** Production-ready Windows installer
