@echo off
REM Cite-Agent Installer - Batch File Wrapper
REM Double-click this file to install Cite-Agent
REM No admin rights required

title Cite-Agent Installer v1.4.0

color 0B
cls
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║   CITE-AGENT INSTALLER                                 ║
echo ║   AI Research Assistant for Windows                    ║
echo ║   Version 1.4.0                                        ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo.
echo This installer will:
echo   [*] Remove any old versions (clean install)
echo   [*] Install Python if needed
echo   [*] Install Cite-Agent from PyPI
echo   [*] Create desktop shortcut
echo   [*] Add to system PATH
echo.
echo Installation takes approximately 2 minutes.
echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PowerShell not found!
    echo.
    echo This installer requires PowerShell.
    echo PowerShell comes pre-installed on Windows 10/11.
    echo.
    echo If you're on Windows 7, please upgrade to Windows 10/11.
    echo.
    pause
    exit /b 1
)

echo [*] Starting installation...
echo.
echo ───────────────────────────────────────────────────────────
echo.

REM Run the PowerShell installer
powershell -ExecutionPolicy Bypass -NoProfile -Command "& { try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Spectating101/nocturnal-archive/production-backend-only/install-clean.ps1')) } catch { Write-Host '[ERROR] Installation failed: ' $_.Exception.Message -ForegroundColor Red; exit 1 } }"

if %errorlevel% neq 0 (
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo.
    echo [X] Installation failed!
    echo.
    echo Common issues:
    echo   1. No internet connection
    echo   2. Firewall blocking downloads
    echo   3. Antivirus blocking Python installation
    echo.
    echo Check the log file at:
    echo   %LOCALAPPDATA%\Cite-Agent\logs\install.log
    echo.
    echo Report issues at:
    echo   https://github.com/Spectating101/cite-agent/issues
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo.
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo [√] Installation complete!
echo.
echo You can now use Cite-Agent:
echo.
echo   1. Double-click "Cite-Agent" icon on Desktop
echo   2. Or search "Cite-Agent" in Start Menu
echo   3. Or type "cite-agent" in any terminal
echo.
echo For R Studio users:
echo   1. Close R Studio if currently open
echo   2. Reopen R Studio
echo   3. Go to Terminal pane (bottom)
echo   4. Type: cite-agent
echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo Press any key to exit...
pause >nul
