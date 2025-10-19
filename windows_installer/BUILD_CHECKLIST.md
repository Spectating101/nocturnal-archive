# Windows Installer Build Checklist

Complete this checklist before distributing the installer to beta testers.

## 📋 Pre-Build Setup

- [ ] **Install Prerequisites on Build Machine (Windows)**
  - [ ] Python 3.8+ installed
  - [ ] Inno Setup 6 installed from https://jrsoftware.org/isdl.php
  - [ ] (Optional) MinGW-w64 for compiling launcher.c

- [ ] **Prepare Assets**
  - [ ] Create `icon.ico` (256x256, use icon.ico.README for guidance)
  - [ ] Write your personal `README_FROM_DEVELOPER.txt` (replace template)
  - [ ] Update version in `build.py` if needed (currently 1.3.6)

- [ ] **Verify cite-agent is Published**
  - [ ] Check PyPI: https://pypi.org/project/cite-agent/1.3.6/
  - [ ] Confirm version number matches `build.py`

## 🔨 Build Process

- [ ] **Run Build Script**
  ```bash
  cd windows_installer
  python build.py
  ```

- [ ] **Build Completes Successfully**
  - [ ] No errors during Python download
  - [ ] No errors during pip install
  - [ ] No errors during Inno Setup compilation
  - [ ] Installer created: `dist/CiteAgent-Setup-v1.3.6.exe`

- [ ] **Check Installer Size**
  - [ ] Should be 60-100 MB
  - [ ] If > 150 MB, something went wrong (check for duplicates)
  - [ ] If < 40 MB, Python might not be bundled

## 🔐 Code Signing (Optional but Recommended)

### Option A: Self-Signed Certificate (Free, shows warning)

- [ ] **Create Self-Signed Certificate**
  ```bash
  create_self_signed_cert.bat
  ```
  - [ ] Enter your name
  - [ ] Enter your email
  - [ ] Set password
  - [ ] `certificate.pfx` created

- [ ] **Sign the Installer**
  ```bash
  sign.bat dist\CiteAgent-Setup-v1.3.6.exe
  ```
  - [ ] Enter certificate password
  - [ ] Signing succeeds
  - [ ] Verify signature shows your name

### Option B: Real Certificate (Paid, no warning)

- [ ] **Purchase Certificate** ($150-$200/year)
  - [ ] From DigiCert, Sectigo, or similar
  - [ ] Save as `certificate.pfx`

- [ ] **Sign the Installer**
  ```bash
  sign.bat dist\CiteAgent-Setup-v1.3.6.exe
  ```

## 🧪 Testing

- [ ] **Test on Clean Windows VM**
  - [ ] Windows 10 or 11 (64-bit)
  - [ ] No Python installed
  - [ ] No cite-agent installed
  - [ ] Fresh install (not an upgrade)

- [ ] **Install from Installer**
  - [ ] Double-click `CiteAgent-Setup-v1.3.6.exe`
  - [ ] (If unsigned) Windows warning appears
  - [ ] Click "More info" → "Run anyway"
  - [ ] Installation completes without errors
  - [ ] Desktop shortcut created

- [ ] **Launch cite-agent**
  - [ ] Double-click desktop shortcut
  - [ ] Terminal window opens
  - [ ] cite-agent starts
  - [ ] Setup prompts for email/password
  - [ ] Setup completes successfully

- [ ] **Test Core Features**
  - [ ] Query: "Tesla revenue" → Returns data
  - [ ] Query: "what about Microsoft?" → Context works
  - [ ] Query: "where am i?" → Shows directory
  - [ ] Query: "help" → Shows help
  - [ ] Query: "quit" → Exits cleanly

- [ ] **Test Auto-Update (Next Day)**
  - [ ] Launch cite-agent again
  - [ ] Wait 24 hours OR delete `~/.cite_agent/.last_update_check`
  - [ ] Should check for updates on startup
  - [ ] (If new version) Should auto-update

- [ ] **Test Uninstall**
  - [ ] Windows Settings → Apps → Cite Agent → Uninstall
  - [ ] Uninstaller runs
  - [ ] Files removed from `C:\Program Files\CiteAgent\`
  - [ ] Desktop shortcut removed
  - [ ] (Config remains at `~/.nocturnal_archive/` by design)

## 📦 Distribution Package

- [ ] **Create Distribution Folder**
  ```
  CiteAgent_v1.3.6_Beta/
  ├── CiteAgent-Setup-v1.3.6.exe
  ├── README_FROM_DEVELOPER.txt
  ├── INSTALL_INSTRUCTIONS.txt
  └── VERIFY_CHECKSUMS.txt
  ```

- [ ] **Generate Checksums**
  ```bash
  cd dist
  certutil -hashfile CiteAgent-Setup-v1.3.6.exe SHA256 > VERIFY_CHECKSUMS.txt
  ```

- [ ] **Verify All Files Present**
  - [ ] Installer .exe
  - [ ] Your personal README
  - [ ] Install instructions
  - [ ] SHA256 checksum

- [ ] **Create ZIP Archive**
  - [ ] Compress folder to `CiteAgent_v1.3.6_Beta.zip`
  - [ ] Test: Extract and verify all files present

## 🚀 Pre-Distribution

- [ ] **Final Smoke Test**
  - [ ] Download the ZIP you'll distribute
  - [ ] Extract on a clean machine
  - [ ] Read README_FROM_DEVELOPER.txt (does it make sense?)
  - [ ] Follow INSTALL_INSTRUCTIONS.txt exactly
  - [ ] Verify installer works

- [ ] **Documentation Check**
  - [ ] README_FROM_DEVELOPER.txt is YOUR words (not template)
  - [ ] Contact email is correct
  - [ ] GitHub links work (if included)
  - [ ] PyPI link works: https://pypi.org/project/cite-agent/1.3.6/

- [ ] **Security Check**
  - [ ] Checksum matches: `certutil -hashfile CiteAgent-Setup-v1.3.6.exe SHA256`
  - [ ] Installer signed (or clear warning about unsigned in README)
  - [ ] No hardcoded credentials in any files

## 📤 Distribution

- [ ] **Choose Distribution Method**
  - [ ] Email to beta testers
  - [ ] Upload to Google Drive / Dropbox (share link)
  - [ ] Host on university server
  - [ ] GitHub Releases (if public)

- [ ] **Send to Beta Testers**
  - [ ] Include link to ZIP file
  - [ ] Brief email explaining what it is
  - [ ] Point to README_FROM_DEVELOPER.txt
  - [ ] Provide your contact info for issues

- [ ] **Monitor for Issues**
  - [ ] Check email for bug reports
  - [ ] Check backend logs for crashes
  - [ ] Track how many users sign up

## ✅ Success Criteria

After sending to beta testers:

- [ ] At least 3 successful installations reported
- [ ] No installer crashes reported
- [ ] cite-agent launches and responds to queries
- [ ] Auto-update works (check after 2 days)
- [ ] Users can quit and relaunch without issues

## 🐛 Common Issues & Fixes

If testers report problems:

**"Windows blocks the installer"**
- Expected with unsigned certificate
- Point them to README section on bypassing warning

**"Installer fails partway through"**
- Check antivirus isn't blocking
- Try "Run as administrator"
- Check disk space (need 200 MB)

**"cite-agent won't launch after install"**
- Verify Python: `"C:\Program Files\CiteAgent\python\python.exe" --version`
- Try manual launch: `cd "C:\Program Files\CiteAgent"` then `CiteAgent.bat`
- Check for error messages

**"Setup rejects email address"**
- Must be academic domain (.edu, .ac.uk, etc.)
- Check spelling carefully
- Try official university email

## 📊 Tracking

Keep a log:

```
Date: ________
Testers notified: ____
Successful installs: ____
Issues reported: ____
Critical bugs: ____
Feature requests: ____
```

## 🎉 Launch Complete!

- [ ] Beta testers have access
- [ ] At least 5 successful installs
- [ ] No critical bugs reported in first 48 hours
- [ ] Auto-update tested and working

**Congratulations!** Your Windows installer is live.

Time to gather feedback and iterate. 🚀
