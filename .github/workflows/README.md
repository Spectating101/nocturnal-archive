# GitHub Actions - Windows Installer Builder

This folder contains workflows to automatically build Windows installers using GitHub's cloud infrastructure.

## Available Workflows

### 1. `build-installer.yml` - Admin Installer
Builds the standard installer that requires admin rights.

**Output:** `Cite-Agent-Installer-v2.0.exe`
**Requires:** Administrator privileges on target machine
**Installs to:** `C:\Program Files\Cite-Agent\`

### 2. `build-installer-both.yml` - Both Versions
Builds two installers:
- Admin version (requires admin rights)
- Per-user version (no admin needed)

**Outputs:**
- `Cite-Agent-Installer-v2.0.exe` (admin)
- `Cite-Agent-Installer-v2.0-PerUser.exe` (per-user)

---

## How to Use

### Step 1: Push Workflows to GitHub

```bash
cd /home/phyrexian/Downloads/llm_automation/project_portfolio/Cite-Agent
git add .github/workflows/
git commit -m "Add GitHub Actions workflow for Windows installer compilation"
git push origin production-backend-only
```

### Step 2: Trigger the Workflow on GitHub

1. Go to: https://github.com/Spectating101/cite-agent
2. Click: **Actions** tab
3. Select: **Build Windows Installer** (or **Build Windows Installers (Admin + Per-User)**)
4. Click: **Run workflow** button (on the right)
5. Select branch: `production-backend-only`
6. Click: **Run workflow** (green button)

**Wait:** 3-5 minutes for GitHub to build

### Step 3: Download the Installer

1. Click on the workflow run (it will have a spinning yellow icon → green checkmark when done)
2. Scroll down to **Artifacts** section
3. Download:
   - `Cite-Agent-Installer-v2.0-Admin.zip` (contains the admin .exe)
   - `Cite-Agent-Installer-v2.0-PerUser.zip` (contains per-user .exe)
4. Extract the ZIP
5. Inside you'll find: `Cite-Agent-Installer-v2.0.exe`

**That's it!** You now have the compiled Windows installer.

---

## Which Version to Use?

### Admin Installer (Recommended)
**Use when:**
- Installing on your own computer
- You have admin rights
- Want system-wide installation

**Pros:**
- ✅ Installs to Program Files (standard location)
- ✅ Available to all users
- ✅ Creates proper uninstaller entry

**Cons:**
- ❌ Requires admin rights
- ❌ UAC prompt appears

### Per-User Installer
**Use when:**
- Installing on locked-down machines (university/company)
- No admin rights available
- Only need it for one user

**Pros:**
- ✅ No admin required
- ✅ No UAC prompt
- ✅ Works on restricted machines

**Cons:**
- ❌ Only installs for current user
- ❌ Installs to AppData folder
- ❌ Other users won't see it

---

## What GitHub Does

When you trigger the workflow:

1. **Spins up Windows VM** (windows-latest = Windows Server 2022)
2. **Installs Inno Setup** via Chocolatey
3. **Compiles the installer** from your `.iss` script
4. **Uploads the .exe** as an artifact (downloadable ZIP)
5. **Cleans up** VM (automatically deleted)

**Cost:** FREE (GitHub gives unlimited Actions for public repos)
**Time:** 3-5 minutes total

---

## Troubleshooting

### Workflow fails: "ISCC.exe not found"

**Cause:** Inno Setup installation failed

**Fix:** Wait a few minutes and retry. Sometimes Chocolatey is slow.

### Workflow fails: "Cannot find .iss file"

**Cause:** Script path is wrong

**Check:** Make sure `windows_installer/cite-agent-installer.iss` exists in repo

### Artifact download is empty

**Cause:** Compilation failed but workflow continued

**Fix:** Click on the workflow run → check logs → see what error happened

### Installer doesn't work after download

**Check:**
- Did you extract the ZIP? (Don't run from inside ZIP)
- Is Windows Defender blocking it? (Right-click → Properties → Unblock)
- Try on a different machine

---

## Advanced: Modify Before Building

### Change Version Number

Edit `windows_installer/cite-agent-installer.iss`:
```iss
#define MyAppVersion "1.3.9"
```

Change to your new version, commit, push, then trigger workflow.

### Change Python Version

Edit `windows_installer/cite-agent-installer.iss`:
```iss
#define PythonVersion "3.11.9"
#define PythonDownloadUrl "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
```

Update both lines, commit, push, trigger.

---

## Comparison: GitHub vs Manual

| Method | Time | Requirements | Cost |
|--------|------|--------------|------|
| **GitHub Actions** | 5 min | GitHub account | Free |
| **Manual Windows** | 2 min | Windows PC + Inno Setup | Free |
| **Cloud VM** | 30 min | Azure/AWS account | $5 |

**Recommendation:** Use GitHub Actions (easiest, no local setup needed)

---

## Files Modified

To enable per-user install, I created:
- `windows_installer/cite-agent-installer-peruser.iss`

**Changes:**
- `PrivilegesRequired=admin` → `lowest`
- `DefaultDirName={autopf}\Cite-Agent` → `{userappdata}\Cite-Agent`

---

## Next Steps After Download

1. ✅ Test installer on clean Windows 11 VM
2. ✅ Verify shortcuts work
3. ✅ Check Python installation works
4. ✅ Test cite-agent launches
5. ✅ Distribute to beta testers

**If everything works:** You're ready to launch! 🚀
