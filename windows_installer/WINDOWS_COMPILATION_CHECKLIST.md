# Windows Compilation Checklist
**For:** You or ChatGPT Codex to compile the installer
**Time:** 5 minutes
**Result:** `Cite-Agent-Installer-v2.0.exe`

---

## Quick Start (3 Steps)

### 1️⃣ Get Files on Windows
Transfer `Cite-Agent-Windows-Compiler-Package.zip` to Windows machine and extract.

### 2️⃣ Install Inno Setup
Download from: https://jrsoftware.org/isdl.php
Install with default settings.

### 3️⃣ Compile
- Open: `windows_installer/cite-agent-installer.iss` in Inno Setup Compiler
- Press: **F9**
- Result: `Cite-Agent-Installer-v2.0.exe` appears

---

## Detailed Checklist

### ☐ Pre-flight Check

- [ ] Windows 10 or 11
- [ ] Administrator access
- [ ] Internet connection (for Inno Setup download)

### ☐ Step 1: Transfer Files

**From Linux:**
```bash
# Package is ready at:
/home/phyrexian/Downloads/llm_automation/project_portfolio/Cite-Agent/Cite-Agent-Windows-Compiler-Package.zip
```

**Transfer options:**
- [ ] USB drive
- [ ] Network share (scp/sftp)
- [ ] Cloud (Dropbox/Drive)
- [ ] Email attachment

**On Windows:**
- [ ] Extract to: `C:\cite-agent-build\`
- [ ] Verify files:
  ```cmd
  dir C:\cite-agent-build\windows_installer
  ```
  Should see: `cite-agent-installer.iss`, `Install-CiteAgent.ps1`, etc.

### ☐ Step 2: Install Inno Setup

- [ ] Visit: https://jrsoftware.org/isdl.php
- [ ] Download: Inno Setup 6.3.3 (or latest 6.x)
- [ ] Run installer
- [ ] Accept defaults (Next, Next, Install)
- [ ] Verify: Start Menu → "Inno Setup Compiler" exists

### ☐ Step 3: Open Script

- [ ] Launch: Inno Setup Compiler
- [ ] File → Open
- [ ] Navigate to: `C:\cite-agent-build\windows_installer\cite-agent-installer.iss`
- [ ] Click: Open
- [ ] Verify: See script with `#define MyAppVersion "1.3.9"`

### ☐ Step 4: Compile

**GUI Method (Recommended):**
- [ ] Press **F9** (or Build → Compile)
- [ ] Wait 5-10 seconds
- [ ] Look for: "Successful compile"

**Or Command Line:**
```cmd
cd C:\cite-agent-build\windows_installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" cite-agent-installer.iss
```

### ☐ Step 5: Verify Output

- [ ] Check file exists:
  ```cmd
  dir C:\cite-agent-build\windows_installer\Cite-Agent-Installer-v2.0.exe
  ```
- [ ] File size: ~15-20 KB
- [ ] Right-click → Properties → Type: Application

### ☐ Step 6: Package for Transfer

**Create ZIP:**
```cmd
cd C:\cite-agent-build\windows_installer
tar -a -c -f Cite-Agent-Installer-v2.0-COMPILED.zip Cite-Agent-Installer-v2.0.exe START_HERE.txt README.txt QUICKSTART.txt
```

**Or manually:**
- [ ] Select: `.exe` + documentation files
- [ ] Right-click → Send to → Compressed folder
- [ ] Name: `Cite-Agent-Installer-v2.0-COMPILED.zip`

### ☐ Step 7 (OPTIONAL): Smoke Test

**Only if you want to test it:**
- [ ] Double-click: `Cite-Agent-Installer-v2.0.exe`
- [ ] Should see: Bilingual welcome screen
- [ ] Click: Next → Next → Install
- [ ] Wait: ~2 minutes (installs Python + cite-agent)
- [ ] Verify: Desktop shortcut "Cite-Agent" appears
- [ ] Test: Double-click shortcut → Terminal opens
- [ ] Type: `quit` to exit

**⚠️ Warning:** This will install cite-agent on the Windows machine!

### ☐ Step 8: Transfer Back

**From Windows to Linux:**
- [ ] Copy `Cite-Agent-Installer-v2.0-COMPILED.zip` back
- [ ] Extract on Linux
- [ ] Move `.exe` to distribution folder

**Final location:**
```bash
/home/phyrexian/Downloads/llm_automation/project_portfolio/Cite-Agent/installers/Cite-Agent-Installer-v2.0.exe
```

---

## Success Criteria

✅ File exists: `Cite-Agent-Installer-v2.0.exe`
✅ File size: 15-20 KB
✅ (Optional) Smoke test passed
✅ Ready for distribution

---

## If Something Goes Wrong

### Compilation Error: "Cannot find file"
**Fix:** Make sure all files from the ZIP are extracted together.

### Inno Setup not found
**Fix:** Install from https://jrsoftware.org/isdl.php

### SmartScreen warning when testing
**Normal:** Unsigned .exe triggers warning. Click "More info" → "Run anyway"

### Python doesn't install during smoke test
**Check:** Internet connection (downloads Python from python.org)

---

## Quick Reference Commands

**Check Inno Setup installed:**
```cmd
dir "C:\Program Files (x86)\Inno Setup 6"
```

**Compile (command line):**
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" cite-agent-installer.iss
```

**Verify output:**
```cmd
dir Cite-Agent-Installer-v2.0.exe
```

---

## Time Estimates

- Transfer files: 2 minutes
- Install Inno Setup: 2 minutes (first time only)
- Compile: 10 seconds
- Smoke test: 3 minutes (optional)
- Transfer back: 2 minutes

**Total: ~5-10 minutes**

---

## For Codex (If Using ChatGPT)

You can paste these instructions into ChatGPT and say:

> "I need to compile a Windows installer using Inno Setup. I have a Windows VM with admin rights. Here are the steps I need to follow: [paste checklist]. Can you guide me through this?"

Codex should be able to:
1. Help troubleshoot any errors
2. Verify the output is correct
3. Create the final package

---

## Next Step After Compilation

Once you have `Cite-Agent-Installer-v2.0.exe`:

1. **Test on clean Windows 11 VM** (final validation)
2. **Distribute to beta testers**
3. **Collect feedback**
4. **Iterate if needed**

---

**Questions?** See `COMPILE_INSTRUCTIONS.md` for detailed troubleshooting.
