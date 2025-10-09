@echo off
REM Windows Installer Build Script
REM Builds a standalone executable and creates Windows installer

echo.
echo ========================================
echo  Nocturnal Archive Windows Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Navigate to project root
cd ..\..

echo.
echo [1/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/4] Building executable with PyInstaller...
pyinstaller --name nocturnal ^
    --onefile ^
    --console ^
    --icon=installers\windows\nocturnal.ico ^
    --add-data "nocturnal_archive;nocturnal_archive" ^
    --hidden-import=nocturnal_archive ^
    --hidden-import=flask ^
    --hidden-import=anthropic ^
    nocturnal_archive\cli_enhanced.py

echo.
echo [3/4] Creating installer with Inno Setup...
REM Check if Inno Setup is installed
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installers\windows\nocturnal-setup.iss
) else (
    echo.
    echo Inno Setup not found. Please install from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo After installing, run this command manually:
    echo "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installers\windows\nocturnal-setup.iss
)

echo.
echo [4/4] Done!
echo.
echo Installer created: installers\windows\dist\nocturnal-archive-setup-1.0.0.exe
echo.
pause
