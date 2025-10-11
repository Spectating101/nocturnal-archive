@echo off
REM Windows Installer Build Script for Cite-Agent v1.0.4
REM Run this on a Windows machine with Python 3.9+ installed

echo ============================================================
echo Building Cite-Agent Windows Installer
echo ============================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    exit /b 1
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Create clean build directory
if exist build_windows rmdir /s /q build_windows
mkdir build_windows
cd build_windows

REM Download the package from PyPI
echo.
echo Downloading cite-agent from PyPI...
pip download cite-agent==1.0.4 --no-deps
if errorlevel 1 (
    echo ERROR: Failed to download cite-agent from PyPI
    exit /b 1
)

REM Extract the package
echo Extracting package...
tar -xf cite_agent-1.0.4.tar.gz
cd cite_agent-1.0.4

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt 2>nul
pip install requests aiohttp python-dotenv pydantic rich keyring

REM Create PyInstaller spec file
echo.
echo Creating PyInstaller spec...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis(
echo     ['cite_agent/cli.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ('cite_agent/*.py', 'cite_agent'),
echo         ('README.md', '.'),
echo         ('LICENSE', '.'),
echo     ],
echo     hiddenimports=[
echo         'cite_agent',
echo         'cite_agent.cli',
echo         'cite_agent.enhanced_ai_agent',
echo         'cite_agent.account_client',
echo         'cite_agent.setup_config',
echo         'requests',
echo         'aiohttp',
echo         'pydantic',
echo         'rich',
echo         'keyring',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='cite-agent',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=True,
echo     disable_windowed_traceback=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon=None,
echo ^)
) > cite-agent.spec

REM Build the executable
echo.
echo Building executable (this may take a few minutes^)...
pyinstaller --clean cite-agent.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

REM Create installer directory
cd ..\..
mkdir installers 2>nul
move build_windows\cite_agent-1.0.4\dist\cite-agent.exe installers\cite-agent-windows-1.0.4.exe

echo.
echo ============================================================
echo SUCCESS! Windows installer created
echo ============================================================
echo.
echo Location: installers\cite-agent-windows-1.0.4.exe
echo Size:
dir installers\cite-agent-windows-1.0.4.exe | find "cite-agent"
echo.
echo To test:
echo   installers\cite-agent-windows-1.0.4.exe --version
echo.
echo To distribute:
echo   1. Upload to GitHub Releases
echo   2. Or host on your own server
echo.

pause
