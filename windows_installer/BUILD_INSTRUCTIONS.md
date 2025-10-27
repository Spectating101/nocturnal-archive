# Building the Cite-Agent .exe Installer

This guide explains how to compile the professional Windows installer from the Inno Setup script.

## Prerequisites

You need **Inno Setup 6.x** installed on a Windows machine.

### Download Inno Setup

1. Visit: https://jrsoftware.org/isdl.php
2. Download: **Inno Setup 6.x** (free)
3. Install with default settings

## Building the Installer

### Method 1: GUI (Easiest)

1. **Open Inno Setup Compiler**
   - Find "Inno Setup Compiler" in Start Menu
   - Or run `C:\Program Files (x86)\Inno Setup 6\Compil32.exe`

2. **Open the script**
   - File → Open
   - Select `cite-agent-installer.iss`

3. **Compile**
   - Build → Compile (or press F9)
   - Wait 5-10 seconds

4. **Output**
   - Success! You'll see: `Cite-Agent-Installer-v2.0.exe`
   - Located in the same folder as the `.iss` file
   - Size: ~15-20 KB

### Method 2: Command Line (For automation)

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" cite-agent-installer.iss
```

## Testing the Installer

### On a Clean Windows VM

1. **Double-click** `Cite-Agent-Installer-v2.0.exe`
2. You should see:
   - Professional installer wizard
   - Bilingual welcome screen (English/Chinese)
   - Progress bars during installation
   - Desktop shortcut created automatically

3. **After installation:**
   - Desktop icon: "Cite-Agent" appears
   - Start Menu: "Cite-Agent" entry
   - Test by double-clicking desktop icon
   - Should open terminal with cite-agent running

### Quick Test Checklist

- [ ] Installer runs without errors
- [ ] Python gets installed (if not present)
- [ ] cite-agent package installs via pip
- [ ] Desktop shortcut works
- [ ] Start Menu shortcut works
- [ ] Can type `cite-agent` in new terminal window
- [ ] R Studio terminal integration works

## What the Installer Does

The `.exe` installer performs these steps:

1. **Extracts files** to `C:\Program Files\Cite-Agent\`
   - PowerShell installation script
   - Documentation files (bilingual)
   - Helper scripts

2. **Runs PowerShell installation script** which:
   - Checks for Python (installs if missing)
   - Fetches latest cite-agent from PyPI
   - Installs cite-agent via pip
   - Adds Python Scripts to PATH
   - Broadcasts PATH change to Windows

3. **Creates shortcuts:**
   - Desktop: `Cite-Agent.lnk`
   - Start Menu: `Cite-Agent` folder with shortcuts

4. **Registers uninstaller** in Windows Settings

## Customization

### Change Version Number

Edit `cite-agent-installer.iss`:

```iss
#define MyAppVersion "1.3.8"
```

Change to your new version, then recompile.

### Change App Icon

1. Create/download a `.ico` file
2. Place it in the installer folder
3. Edit the script:

```iss
SetupIconFile=my-custom-icon.ico
```

### Modify Installation Steps

Edit the `[Run]` section in `cite-agent-installer.iss` to add/remove post-install actions.

## Distribution

### For Beta Users

Simply distribute: **`Cite-Agent-Installer-v2.0.exe`**

That's it! One file, no dependencies, no zip extraction.

Users just:
1. Download `.exe`
2. Double-click
3. Click "Next, Next, Install"
4. Done!

### For Production (Code Signing)

To remove Windows SmartScreen warnings, you need a code signing certificate:

1. **Get a certificate** ($100-400/year):
   - DigiCert
   - Sectigo
   - SSL.com

2. **Sign the installer:**
   ```cmd
   signtool sign /f your-certificate.pfx /p password /t http://timestamp.digicert.com Cite-Agent-Installer-v2.0.exe
   ```

3. **Distribute signed .exe**
   - No more warnings
   - Professional trust

## Troubleshooting

### Error: "Cannot find PowerShell script"

Make sure `Install-CiteAgent.ps1` is in the same folder as the `.iss` file.

### Error: "Failed to install Python"

The PowerShell script downloads Python automatically. Check:
- Internet connection
- Windows Firewall settings

### Desktop shortcut doesn't work

If shortcut shows "python not found":
- The user needs to restart their computer
- PATH changes need a reboot to take full effect

## File Structure

After building, your folder should contain:

```
windows_installer/
├── cite-agent-installer.iss          # Inno Setup script
├── Install-CiteAgent.ps1              # PowerShell installer
├── cite-agent.bat                     # Helper launcher
├── START_HERE.txt                     # Bilingual instructions
├── README.txt                         # Full documentation
├── QUICKSTART.txt                     # Usage examples
├── CHANGELOG.txt                      # Version history
├── LICENSE.txt                        # License
└── Cite-Agent-Installer-v2.0.exe     # ← Final product! (generated)
```

## Next Steps

1. **Build the .exe** using instructions above
2. **Test on clean Windows VM**
3. **Distribute to beta testers**
4. **Collect feedback**
5. **(Optional) Code sign for production**

---

**Need help?** Open an issue on GitHub or contact the development team.

**Version:** 2.0
**Last Updated:** 2025-10-24
