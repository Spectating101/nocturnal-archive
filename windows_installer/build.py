#!/usr/bin/env python3
"""
Windows Installer Builder for Cite Agent
Bundles Python runtime + cite-agent into single installer
"""

import os
import sys
import urllib.request
import zipfile
import subprocess
import shutil
from pathlib import Path

# Configuration
PYTHON_VERSION = "3.13.1"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
CITE_AGENT_VERSION = "1.3.7"

class WindowsInstallerBuilder:
    def __init__(self):
        self.root = Path(__file__).parent
        self.build_dir = self.root / "build"
        self.dist_dir = self.root / "dist"
        self.python_dir = self.build_dir / "python"
        self.app_dir = self.build_dir / "CiteAgent"

    def clean(self):
        """Clean previous builds"""
        print("🧹 Cleaning previous builds...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        print("✅ Clean complete")

    def download_python(self):
        """Download embedded Python"""
        print(f"📥 Downloading Python {PYTHON_VERSION} embedded...")

        zip_path = self.build_dir / f"python-{PYTHON_VERSION}.zip"

        if not zip_path.exists():
            urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path)
            print(f"✅ Downloaded to {zip_path}")
        else:
            print(f"✅ Using cached {zip_path}")

        # Extract
        print("📦 Extracting Python...")
        self.python_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.python_dir)
        print(f"✅ Python extracted to {self.python_dir}")

        # Enable pip in embedded Python
        pth_file = self.python_dir / f"python{PYTHON_VERSION.replace('.', '')[:3]}._pth"
        if pth_file.exists():
            content = pth_file.read_text()
            if "import site" in content:
                # Already enabled
                pass
            else:
                # Uncomment import site
                content = content.replace("#import site", "import site")
                pth_file.write_text(content)
                print("✅ Enabled pip in embedded Python")

    def install_pip(self):
        """Install pip into embedded Python"""
        print("📦 Installing pip...")

        # Download get-pip.py
        get_pip = self.build_dir / "get-pip.py"
        if not get_pip.exists():
            urllib.request.urlretrieve(
                "https://bootstrap.pypa.io/get-pip.py",
                get_pip
            )

        # Run get-pip.py
        python_exe = self.python_dir / "python.exe"
        result = subprocess.run(
            [str(python_exe), str(get_pip)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ pip installed")
        else:
            print(f"⚠️  pip install had issues (may already be installed)")
            print(result.stderr[:200])

    def install_cite_agent(self):
        """Install cite-agent and dependencies"""
        print(f"📦 Installing cite-agent v{CITE_AGENT_VERSION}...")

        python_exe = self.python_dir / "python.exe"
        pip_exe = self.python_dir / "Scripts" / "pip.exe"

        # Try using pip directly first
        if pip_exe.exists():
            cmd = [str(pip_exe), "install", f"cite-agent=={CITE_AGENT_VERSION}"]
        else:
            cmd = [str(python_exe), "-m", "pip", "install", f"cite-agent=={CITE_AGENT_VERSION}"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("✅ cite-agent installed")
        else:
            print("❌ Failed to install cite-agent")
            print(result.stderr)
            sys.exit(1)

    def create_launcher(self):
        """Create launcher batch script"""
        print("🚀 Creating launcher...")

        launcher_bat = self.app_dir / "CiteAgent.bat"
        launcher_bat.parent.mkdir(parents=True, exist_ok=True)

        launcher_content = f'''@echo off
REM Cite Agent Launcher
setlocal

REM Get the directory where this script is located
set "APP_DIR=%~dp0"

REM Set Python path
set "PYTHON_HOME=%APP_DIR%python"
set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\\Scripts;%PATH%"

REM Run cite-agent
"%PYTHON_HOME%\\python.exe" -m cite_agent.cli %*

endlocal
'''
        launcher_bat.write_text(launcher_content)
        print(f"✅ Launcher created at {launcher_bat}")

    def copy_files(self):
        """Copy all files to app directory"""
        print("📋 Copying files to app directory...")

        self.app_dir.mkdir(parents=True, exist_ok=True)

        # Copy Python
        app_python = self.app_dir / "python"
        if app_python.exists():
            shutil.rmtree(app_python)
        shutil.copytree(self.python_dir, app_python)
        print(f"✅ Copied Python to {app_python}")

    def create_inno_script(self):
        """Generate Inno Setup script"""
        print("📝 Creating Inno Setup script...")

        iss_content = f'''
; Cite Agent Installer Script for Inno Setup

#define MyAppName "Cite Agent"
#define MyAppVersion "{CITE_AGENT_VERSION}"
#define MyAppPublisher "Yuan Ze University"
#define MyAppURL "https://github.com/yourusername/Cite-Agent"
#define MyAppExeName "CiteAgent.bat"

[Setup]
AppId={{{{5F8A9B3C-1D2E-4F5A-8B9C-3D4E5F6A7B8C}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
OutputDir=..\\dist
OutputBaseFilename=CiteAgent-Setup-v{CITE_AGENT_VERSION}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=icon.ico
UninstallDisplayIcon={{app}}\\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "{{#SourcePath}}\\build\\CiteAgent\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then
  begin
    MsgBox('This application requires 64-bit Windows.', mbError, MB_OK);
    Result := False;
  end;
end;
'''

        iss_path = self.root / "installer.iss"
        iss_path.write_text(iss_content)
        print(f"✅ Inno Setup script created at {iss_path}")

        return iss_path

    def create_icon(self):
        """Create a simple icon file (placeholder)"""
        icon_path = self.root / "icon.ico"
        if not icon_path.exists():
            # Create a placeholder - user should replace with real icon
            print("⚠️  No icon.ico found - will use default")
            # For now, just create empty file so Inno Setup doesn't fail
            icon_path.write_bytes(b'')
        return icon_path

    def compile_installer(self, iss_path):
        """Compile with Inno Setup"""
        print("🔨 Compiling installer with Inno Setup...")

        # Common Inno Setup locations
        iscc_paths = [
            r"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
            r"C:\\Program Files\\Inno Setup 6\\ISCC.exe",
        ]

        iscc_exe = None
        for path in iscc_paths:
            if os.path.exists(path):
                iscc_exe = path
                break

        if not iscc_exe:
            print("❌ Inno Setup not found!")
            print("📥 Please download from: https://jrsoftware.org/isdl.php")
            print("   Then re-run this script")
            sys.exit(1)

        result = subprocess.run(
            [iscc_exe, str(iss_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ Installer compiled successfully!")
            installer_path = self.dist_dir / f"CiteAgent-Setup-v{CITE_AGENT_VERSION}.exe"
            print(f"📦 Installer: {installer_path}")
            return installer_path
        else:
            print("❌ Compilation failed")
            print(result.stderr)
            sys.exit(1)

    def build(self):
        """Run complete build process"""
        print("=" * 60)
        print("🏗️  Building Cite Agent Windows Installer")
        print("=" * 60)

        try:
            self.clean()
            self.download_python()
            self.install_pip()
            self.install_cite_agent()
            self.copy_files()
            self.create_launcher()
            self.create_icon()
            iss_path = self.create_inno_script()
            installer_path = self.compile_installer(iss_path)

            print("\n" + "=" * 60)
            print("✅ BUILD COMPLETE!")
            print("=" * 60)
            print(f"📦 Installer: {installer_path}")
            print(f"📏 Size: {installer_path.stat().st_size / 1024 / 1024:.1f} MB")
            print("\n🚀 Ready to distribute!")

        except KeyboardInterrupt:
            print("\n⚠️  Build cancelled")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Build failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    if sys.platform != "win32":
        print("⚠️  This script must be run on Windows")
        sys.exit(1)

    builder = WindowsInstallerBuilder()
    builder.build()

if __name__ == "__main__":
    main()
