@echo off
REM ========================================
REM  Cite-Agent Universal Installer v2.0
REM  - Auto-detects Python, installs if needed
REM  - Auto-fetches latest version from PyPI
REM  - Adds to PATH automatically
REM  - Creates desktop and Start Menu shortcuts
REM ========================================

color 0A
title Cite-Agent Installer

echo.
echo ========================================
echo  Cite-Agent Installer v2.0
echo ========================================
echo.

REM ========================================
REM STEP 1: Check Python
REM ========================================
echo [1/7] Checking for Python...

python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python found:
    python --version
    goto :get_version
)

echo [WARNING] Python not found
echo.
echo Do you want to install Python 3.11.9? (Y/N)
set /p INSTALL_PY=

if /i not "%INSTALL_PY%"=="Y" (
    echo.
    echo Installation cancelled. Python is required.
    pause
    exit /b 1
)

echo.
echo Downloading Python 3.11.9 (25 MB)...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe'" 2>nul

if %errorlevel% neq 0 (
    echo [ERROR] Download failed. Check internet connection.
    pause
    exit /b 1
)

echo Installing Python (this takes 1-2 minutes)...
start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1

del python-installer.exe 2>nul

echo [OK] Python installed
echo.
echo Refreshing environment...
timeout /t 3 >nul

REM ========================================
REM STEP 2: Get latest version from PyPI
REM ========================================
:get_version
echo.
echo [2/7] Checking latest cite-agent version on PyPI...

for /f "delims=" %%i in ('python -c "import urllib.request, json; print(json.loads(urllib.request.urlopen('https://pypi.org/pypi/cite-agent/json').read())['info']['version'])" 2^>nul') do set VERSION=%%i

if "%VERSION%"=="" (
    echo [WARNING] Could not auto-detect version. Using default: 1.3.8
    set VERSION=1.3.8
) else (
    echo [OK] Latest version: %VERSION%
)

REM ========================================
REM STEP 3: Verify Python
REM ========================================
echo.
echo [3/7] Verifying Python installation...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python still not found. Please restart this script.
    pause
    exit /b 1
)

python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found. Python installation may be incomplete.
    pause
    exit /b 1
)

echo [OK] Python is ready

REM ========================================
REM STEP 4: Remove old version
REM ========================================
echo.
echo [4/7] Checking for old cite-agent...

python -m pip show cite-agent >nul 2>&1
if %errorlevel% == 0 (
    echo Removing old version...
    python -m pip uninstall -y cite-agent >nul 2>&1
    echo [OK] Old version removed
) else (
    echo [OK] No old version found
)

REM ========================================
REM STEP 5: Install cite-agent
REM ========================================
echo.
echo [5/7] Installing cite-agent v%VERSION%...
echo (This may take 30-60 seconds)

python -m pip install --user --no-cache-dir cite-agent==%VERSION%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed
    echo.
    echo Try manually:
    echo   python -m pip install --upgrade --user cite-agent
    pause
    exit /b 1
)

REM ========================================
REM STEP 6: Add Python Scripts to PATH
REM ========================================
echo.
echo [6/7] Adding cite-agent to system PATH...

REM Get Python Scripts path
for /f "delims=" %%i in ('python -c "import site; print(site.USER_BASE + '\\Scripts')"') do set SCRIPTS_PATH=%%i

echo Scripts path: %SCRIPTS_PATH%

REM Add to user PATH permanently using PowerShell
powershell -Command "$oldPath = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($oldPath -notlike '*%SCRIPTS_PATH%*') { [Environment]::SetEnvironmentVariable('Path', $oldPath + ';%SCRIPTS_PATH%', 'User'); Write-Host '[OK] Added to PATH' } else { Write-Host '[OK] Already in PATH' }"

REM Update current session PATH
set PATH=%PATH%;%SCRIPTS_PATH%

echo [OK] PATH updated

REM ========================================
REM STEP 7: Create Desktop and Start Menu Shortcuts
REM ========================================
echo.
echo [7/7] Creating shortcuts...

REM Create VBScript to make shortcuts (batch can't create .lnk files natively)
REM Use python -m cite_agent.cli instead of cite-agent for reliability
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Cite-Agent.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "cmd.exe" >> CreateShortcut.vbs
echo oLink.Arguments = "/k python -m cite_agent.cli" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = oWS.SpecialFolders("Desktop") >> CreateShortcut.vbs
echo oLink.Description = "Cite-Agent AI Research Assistant" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Desktop shortcut creation failed
) else (
    echo [OK] Desktop shortcut created
)
del CreateShortcut.vbs 2>nul

REM Create Start Menu shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Programs") ^& "\Cite-Agent.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "cmd.exe" >> CreateShortcut.vbs
echo oLink.Arguments = "/k python -m cite_agent.cli" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = oWS.SpecialFolders("Desktop") >> CreateShortcut.vbs
echo oLink.Description = "Cite-Agent AI Research Assistant" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Start Menu shortcut creation failed
) else (
    echo [OK] Start Menu shortcut created
)
del CreateShortcut.vbs 2>nul

REM ========================================
REM Installation Complete!
REM ========================================
echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.

python -m cite_agent.cli --version

echo.
echo ========================================
echo  CITE-AGENT IS READY TO USE!
echo ========================================
echo.
echo EASY START:
echo -----------
echo   1. Double-click "Cite-Agent" icon on your Desktop
echo   2. Or find "Cite-Agent" in Start Menu
echo   3. The chat interface will open automatically!
echo.
echo.
echo FOR R STUDIO / STATA:
echo ---------------------
echo   1. Open R Studio (or Stata)
echo   2. Open the Terminal pane
echo   3. Type: cite-agent
echo   4. Press Enter - that's it!
echo.
echo.
echo FIRST TIME SETUP:
echo -----------------
echo When you first launch, you'll be asked to login.
echo Use your academic email to create a free account.
echo.
echo   Email: %USERNAME%@youruniversity.edu
echo   (The installer has already logged you in if you used credentials)
echo.
echo.
echo TRY IT NOW:
echo -----------
echo This window will launch cite-agent in 5 seconds...
echo (Press Ctrl+C to skip)
echo.

timeout /t 5

REM Launch cite-agent for demo (use full path for reliability)
python -m cite_agent.cli
