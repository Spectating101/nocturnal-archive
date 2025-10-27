@echo off
REM ========================================
REM  Cite-Agent UNIVERSAL INSTALLER v2.1
REM  THE ONLY FILE YOU NEED TO RUN
REM  Right-click → Run as Administrator
REM ========================================

color 0A
title Cite-Agent Installer v2.1

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║     CITE-AGENT INSTALLER v2.1                      ║
echo ║     AI Research Assistant for Windows              ║
echo ╚════════════════════════════════════════════════════╝
echo.
echo This installer will:
echo   [1] Check/Install Python 3.11
echo   [2] Install cite-agent from PyPI
echo   [3] Add to PATH automatically
echo   [4] Create desktop shortcuts
echo.
echo Estimated time: 2-3 minutes
echo.
pause

REM ========================================
REM STEP 1: Check Python
REM ========================================
echo.
echo [1/6] Checking for Python...
echo.

python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python found:
    python --version
    goto :install_cite_agent
)

echo [!] Python not found. Installing Python 3.11.9...
echo.
echo Downloading Python installer (25 MB)...
powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'}"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Download failed. Check internet connection.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing Python (this takes 1-2 minutes)...
echo Please wait, do not close this window...
start /wait %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1

del %TEMP%\python-installer.exe 2>nul

echo.
echo [OK] Python installed successfully
echo.
echo Refreshing environment...
timeout /t 3 /nobreak >nul

REM ========================================
REM STEP 2: Verify Python
REM ========================================
:install_cite_agent
echo.
echo [2/6] Verifying Python installation...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python still not found after installation.
    echo    Please restart your computer and run this installer again.
    echo.
    pause
    exit /b 1
)

python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found. Python installation may be incomplete.
    echo    Please restart your computer and run this installer again.
    echo.
    pause
    exit /b 1
)

echo [OK] Python and pip are ready
python --version

REM ========================================
REM STEP 3: Remove old cite-agent
REM ========================================
echo.
echo [3/6] Checking for old cite-agent installation...
echo.

python -m pip show cite-agent >nul 2>&1
if %errorlevel% == 0 (
    echo Found old version. Removing...
    python -m pip uninstall -y cite-agent >nul 2>&1
    echo [OK] Old version removed
) else (
    echo [OK] No old version found
)

REM ========================================
REM STEP 4: Install cite-agent
REM ========================================
echo.
echo [4/6] Installing cite-agent from PyPI...
echo (This may take 30-60 seconds)
echo.

python -m pip install --user --upgrade --no-cache-dir cite-agent

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed
    echo.
    echo Try running manually:
    echo   python -m pip install --upgrade --user cite-agent
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] cite-agent installed successfully

REM ========================================
REM STEP 5: Add to PATH
REM ========================================
echo.
echo [5/6] Adding cite-agent to system PATH...
echo.

REM Get Python Scripts path
for /f "delims=" %%i in ('python -c "import site; print(site.USER_BASE + '\\Scripts')"') do set SCRIPTS_PATH=%%i

echo Scripts path: %SCRIPTS_PATH%

REM Add to user PATH using PowerShell
powershell -Command "& {$oldPath = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($oldPath -notlike '*%SCRIPTS_PATH%*') { [Environment]::SetEnvironmentVariable('Path', $oldPath + ';%SCRIPTS_PATH%', 'User'); Write-Host '[OK] Added to PATH' } else { Write-Host '[OK] Already in PATH' }}"

REM Update current session
set PATH=%PATH%;%SCRIPTS_PATH%

echo.
echo [OK] PATH updated

REM ========================================
REM STEP 6: Create Shortcuts
REM ========================================
echo.
echo [6/6] Creating desktop and Start Menu shortcuts...
echo.

REM Create VBScript for shortcut creation
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Cite-Agent.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "cmd.exe" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Arguments = "/k python -m cite_agent.cli" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = oWS.SpecialFolders("Desktop") >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Cite-Agent AI Research Assistant" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Desktop shortcut creation failed (continuing anyway)
) else (
    echo [OK] Desktop shortcut created
)

REM Create Start Menu shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = oWS.SpecialFolders("Programs") ^& "\Cite-Agent.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "cmd.exe" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Arguments = "/k python -m cite_agent.cli" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = oWS.SpecialFolders("Desktop") >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Cite-Agent AI Research Assistant" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Start Menu shortcut creation failed (continuing anyway)
) else (
    echo [OK] Start Menu shortcut created
)

del "%TEMP%\CreateShortcut.vbs" 2>nul

REM ========================================
REM INSTALLATION COMPLETE!
REM ========================================
echo.
echo ════════════════════════════════════════════════════
echo   INSTALLATION COMPLETE!
echo ════════════════════════════════════════════════════
echo.

python -m cite_agent.cli --version 2>nul
if %errorlevel% neq 0 (
    echo cite-agent is installed but version check failed.
    echo This is normal - the command will work after restart.
)

echo.
echo ════════════════════════════════════════════════════
echo   HOW TO START:
echo ════════════════════════════════════════════════════
echo.
echo   METHOD 1: Double-click "Cite-Agent" icon on Desktop
echo            (Easiest - RECOMMENDED)
echo.
echo   METHOD 2: Start Menu -^> Search "Cite-Agent"
echo.
echo   METHOD 3: Open any terminal, type: cite-agent
echo.
echo ════════════════════════════════════════════════════
echo   FOR R STUDIO / STATA USERS:
echo ════════════════════════════════════════════════════
echo.
echo   1. Open R Studio (or Stata)
echo   2. Find the Terminal pane (usually at bottom)
echo   3. Type: cite-agent
echo   4. Press Enter
echo.
echo   IMPORTANT: If R Studio was open during install,
echo   close it and reopen it for PATH changes to take effect.
echo.
echo ════════════════════════════════════════════════════
echo   FIRST TIME SETUP:
echo ════════════════════════════════════════════════════
echo.
echo   When you first launch, you'll see a login screen.
echo   Use your academic email to create a free account:
echo.
echo     Example: john.smith@university.edu
echo.
echo   Or press Enter to use demo mode (no login needed)
echo.
echo ════════════════════════════════════════════════════
echo.
echo Press any key to launch Cite-Agent now...
echo (or close this window to exit)
pause >nul

REM Launch cite-agent
echo.
echo Launching Cite-Agent...
echo.
python -m cite_agent.cli
