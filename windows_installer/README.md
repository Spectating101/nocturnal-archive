# Windows Installer Assets

This directory contains the source files for the **Cite-Agent for Windows** installer.
Only the compiled `.exe` produced by Inno Setup is intended for end users.

## Build Workflow (recap)

1. Open `cite-agent-installer.iss` in Inno Setup 6.x (or run `ISCC cite-agent-installer.iss`).
2. Inno Setup copies the supporting files in this folder and generates `Cite-Agent-Installer-v2.0.exe`.
3. The generated `.exe` is the *only* file you distribute or double-click.

## File Guide

| File | Purpose |
|------|---------|
| `cite-agent-installer.iss` | Inno Setup configuration—single source of version numbers and metadata. |
| `Install-CiteAgent.ps1` | GUI bootstrapper run by the wizard. Installs Python (if needed), installs `cite-agent`, updates PATH, creates shortcuts. It now refuses to run when launched directly. |
| `cite-agent.bat` | Launcher used by shortcuts. Tries `py` first, then `python`, and prints a helpful message if neither exists. |
| `BUILD_INSTRUCTIONS.md` | Detailed steps for building and testing the installer. |
| `START_HERE.txt`, `README.txt`, `QUICKSTART.txt`, `CHANGELOG.txt`, `LICENSE.txt` | User-facing docs copied into the install directory. |

## Do **Not** Run These Directly

- `Install-CiteAgent.ps1` – shows a warning unless invoked by the official `.exe`.
- Legacy launch scripts or old batch installers (removed) are kept out of the build to avoid confusion.

If you need to test the install flow, always rebuild and run the `.exe` so you see the full wizard + progress UI. Use a clean Windows VM when possible.
