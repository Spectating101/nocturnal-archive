#!/usr/bin/env python3
"""
Self-Contained Builder - Creates standalone executable with all dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile

class SelfContainedBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.gui_dir = self.project_root / "vertikal-gui"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        
    def build_executable(self):
        """Build self-contained executable using PyInstaller"""
        print("🏗️ Building self-contained executable...")
        
        # Clean previous builds
        self._clean_build_dirs()
        
        # Install PyInstaller if not available
        self._install_pyinstaller()
        
        # Create spec file
        spec_file = self._create_spec_file()
        
        # Build executable
        self._run_pyinstaller(spec_file)
        
        # Post-build steps
        self._post_build_steps()
        
        print("✅ Self-contained executable built successfully!")
        print(f"📁 Output: {self.dist_dir}")
    
    def _clean_build_dirs(self):
        """Clean build directories"""
        print("🧹 Cleaning build directories...")
        
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed: {dir_path}")
    
    def _install_pyinstaller(self):
        """Install PyInstaller if not available"""
        try:
            import PyInstaller
            print("✅ PyInstaller already installed")
        except ImportError:
            print("📦 Installing PyInstaller...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    def _create_spec_file(self):
        """Create PyInstaller spec file"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{self.gui_dir / "vertikal_simple_gui.py"}'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('{self.gui_dir / "api_key_manager.py"}', '.'),
        ('{self.project_root / "vertikal" / "__init__.py"}', 'vertikal'),
    ],
    hiddenimports=[
        'groq',
        'cryptography',
        'requests',
        'pathlib',
        'json',
        'base64',
        'getpass',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='vertikal-assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
        
        spec_file = self.project_root / "vertikal.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        print(f"✅ Created spec file: {spec_file}")
        return spec_file
    
    def _run_pyinstaller(self, spec_file):
        """Run PyInstaller with spec file"""
        print("🔨 Running PyInstaller...")
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ PyInstaller failed:")
            print(result.stderr)
            raise RuntimeError("PyInstaller build failed")
        
        print("✅ PyInstaller completed successfully")
    
    def _post_build_steps(self):
        """Post-build steps"""
        print("🔧 Post-build steps...")
        
        # Find the executable
        exe_name = "vertikal-assistant.exe" if os.name == 'nt' else "vertikal-assistant"
        exe_path = self.dist_dir / exe_name
        
        if not exe_path.exists():
            raise RuntimeError(f"Executable not found: {exe_path}")
        
        # Create version info
        self._create_version_info()
        
        # Create README for distribution
        self._create_distribution_readme()
        
        print(f"✅ Executable ready: {exe_path}")
    
    def _create_version_info(self):
        """Create version info file"""
        version_info = {
            'version': '1.0.0',
            'build_date': str(Path().cwd()),
            'python_version': sys.version,
            'platform': sys.platform
        }
        
        version_file = self.dist_dir / "version.json"
        import json
        with open(version_file, 'w') as f:
            json.dump(version_info, f, indent=2)
        
        print(f"✅ Created version info: {version_file}")
    
    def _create_distribution_readme(self):
        """Create README for distribution"""
        readme_content = '''# Vertikal Assistant - Self-Contained Executable

## Quick Start

1. **Run the executable**: Double-click `vertikal-assistant.exe` (Windows) or `vertikal-assistant` (Linux/Mac)

2. **Setup API key**: Enter your Groq API key when prompted
   - Get free key at: https://console.groq.com/

3. **Start chatting**: The assistant will open in your terminal

## Features

- ✅ Self-contained (no Python installation required)
- ✅ All dependencies included
- ✅ Secure API key storage
- ✅ File-aware ChatGPT assistant
- ✅ Works in RStudio Terminal

## Usage

```bash
# Windows
vertikal-assistant.exe

# Linux/Mac
./vertikal-assistant
```

## Support

- GitHub: https://github.com/yourusername/vertikal
- Issues: https://github.com/yourusername/vertikal/issues

## Version

Check `version.json` for build information.
'''
        
        readme_file = self.dist_dir / "README.txt"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"✅ Created distribution README: {readme_file}")

class WindowsInstallerBuilder:
    """Build Windows installer using NSIS"""
    
    def __init__(self, dist_dir):
        self.dist_dir = Path(dist_dir)
        self.installer_dir = self.dist_dir.parent / "installer"
        self.installer_dir.mkdir(exist_ok=True)
    
    def create_nsis_script(self):
        """Create NSIS installer script"""
        nsis_script = f'''# Vertikal Assistant Installer Script
!define APPNAME "Vertikal Assistant"
!define COMPANYNAME "Vertikal"
!define DESCRIPTION "File-aware ChatGPT assistant for RStudio"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/yourusername/vertikal"
!define UPDATEURL "https://github.com/yourusername/vertikal/releases"
!define ABOUTURL "https://github.com/yourusername/vertikal"
!define INSTALLSIZE 50000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\\${{APPNAME}}"
Name "${{APPNAME}}"
outFile "${{OUTDIR}}\\VertikalAssistantSetup.exe"

!include LogicLib.nsh

page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${{If}} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${{EndIf}}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    file /r "{self.dist_dir}\\*"
    
    writeUninstaller "$INSTDIR\\uninstall.exe"
    
    createDirectory "$SMPROGRAMS\\${{APPNAME}}"
    createShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\vertikal-assistant.exe"
    createShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\vertikal-assistant.exe"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayName" "${{APPNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayIcon" "$INSTDIR\\vertikal-assistant.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "Publisher" "${{COMPANYNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "HelpLink" "${{HELPURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "URLUpdateInfo" "${{UPDATEURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "URLInfoAbout" "${{ABOUTURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayVersion" "${{VERSIONMAJOR}}.${{VERSIONMINOR}}.${{VERSIONBUILD}}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "VersionMajor" ${{VERSIONMAJOR}}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "VersionMinor" ${{VERSIONMINOR}}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "EstimatedSize" ${{INSTALLSIZE}}
sectionEnd

section "uninstall"
    delete "$INSTDIR\\uninstall.exe"
    rmDir /r "$INSTDIR"
    
    delete "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk"
    rmDir "$SMPROGRAMS\\${{APPNAME}}"
    delete "$DESKTOP\\${{APPNAME}}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"
sectionEnd
'''
        
        nsis_file = self.installer_dir / "installer.nsi"
        with open(nsis_file, 'w') as f:
            f.write(nsis_script)
        
        print(f"✅ Created NSIS script: {nsis_file}")
        return nsis_file
    
    def build_installer(self):
        """Build Windows installer"""
        if os.name != 'nt':
            print("⚠️ Windows installer can only be built on Windows")
            return None
        
        nsis_script = self.create_nsis_script()
        
        # Check if NSIS is installed
        try:
            subprocess.run(['makensis', '/VERSION'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ NSIS not found. Please install NSIS to build Windows installer.")
            print("   Download from: https://nsis.sourceforge.io/")
            return None
        
        # Build installer
        print("🔨 Building Windows installer...")
        result = subprocess.run(['makensis', str(nsis_script)], cwd=self.installer_dir)
        
        if result.returncode == 0:
            installer_path = self.installer_dir / "VertikalAssistantSetup.exe"
            print(f"✅ Windows installer built: {installer_path}")
            return installer_path
        else:
            print("❌ Failed to build Windows installer")
            return None

def main():
    """Main entry point"""
    print("🏗️ Vertikal Self-Contained Builder")
    print("=" * 40)
    
    builder = SelfContainedBuilder()
    
    # Build executable
    builder.build_executable()
    
    # Build Windows installer if on Windows
    if os.name == 'nt':
        installer_builder = WindowsInstallerBuilder(builder.dist_dir)
        installer_path = installer_builder.build_installer()
        
        if installer_path:
            print(f"\n🎉 Build complete!")
            print(f"📁 Executable: {builder.dist_dir}")
            print(f"📦 Installer: {installer_path}")
        else:
            print(f"\n✅ Executable built: {builder.dist_dir}")
    else:
        print(f"\n✅ Executable built: {builder.dist_dir}")

if __name__ == "__main__":
    main()
