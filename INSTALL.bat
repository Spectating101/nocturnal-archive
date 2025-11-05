@echo off
title Cite-Agent Installer
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
echo Starting installation...
echo This will take approximately 2 minutes.
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Run the web installer via PowerShell (keep window open)
powershell -ExecutionPolicy Bypass -NoProfile -NoExit -Command "& {Write-Host 'Downloading installer...' -ForegroundColor Yellow; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Spectating101/nocturnal-archive/production-backend-only/install-clean.ps1')); Write-Host ''; Write-Host 'Installation complete! Close this window and open a NEW PowerShell to test.' -ForegroundColor Green; Write-Host 'Type: cite-agent --version' -ForegroundColor Yellow}"

if %errorlevel% equ 0 (
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
    echo Installation complete!
    echo.
    echo You can now use Cite-Agent:
    echo   1. Double-click "Cite-Agent" on Desktop
    echo   2. Type "cite-agent" in terminal
    echo   3. Use in R Studio terminal
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
) else (
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
    echo Installation failed!
    echo.
    echo Please check:
    echo   - Internet connection
    echo   - Firewall settings
    echo.
    echo Or try the manual command in PowerShell:
    echo   iwr -useb https://raw.githubusercontent.com/Spectating101/nocturnal-archive/production-backend-only/install-clean.ps1 ^| iex
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
)

pause
