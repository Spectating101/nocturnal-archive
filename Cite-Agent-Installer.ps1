# Cite-Agent Simple Installer
# Right-click this file → Run with PowerShell

# Force console to stay open
$Host.UI.RawUI.WindowTitle = "Cite-Agent Installer"

# Don't let it close on error
$ErrorActionPreference = "Continue"

# Self-elevation check
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    # Not admin, but that's okay - we don't need admin
    Write-Host "Running in user mode (no admin required)" -ForegroundColor Green
}

Start-Sleep -Milliseconds 500

# Show simple console progress if GUI fails to load
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "║   CITE-AGENT INSTALLER                                 ║" -ForegroundColor Cyan
Write-Host "║   AI Research Assistant for Windows                    ║" -ForegroundColor Cyan
Write-Host "║   Version 1.4.0                                        ║" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Configuration
$CITE_AGENT_VERSION = "1.4.0"
$PYTHON_VERSION = "3.11.9"
$PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
$INSTALL_ROOT = "$env:LOCALAPPDATA\Cite-Agent"
$LOG_FILE = "$INSTALL_ROOT\logs\install.log"

# Setup logging
function Initialize-Log {
    $logDir = Split-Path $LOG_FILE -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    "=== Cite-Agent Installation - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Out-File $LOG_FILE -Encoding UTF8
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "$timestamp | $Message" | Out-File $LOG_FILE -Append -Encoding UTF8
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor Green
    Write-Log $Message
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor Red
    Write-Log "ERROR: $Message"
}

try {
    Initialize-Log
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    Write-Host "Downloading installer script from GitHub..." -ForegroundColor Yellow
    Write-Host ""

    # Download and run the web installer directly
    $installerUrl = "https://raw.githubusercontent.com/Spectating101/nocturnal-archive/production-backend-only/install-clean.ps1"

    Write-Log "Fetching installer from: $installerUrl"

    $webClient = New-Object System.Net.WebClient
    $installerScript = $webClient.DownloadString($installerUrl)

    Write-Success "Installer downloaded successfully"
    Write-Host ""
    Write-Host "Starting installation..." -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""

    # Execute the installer
    Invoke-Expression $installerScript

} catch {
    Write-Error-Custom "Installation failed: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check your internet connection"
    Write-Host "  2. Check firewall settings"
    Write-Host "  3. Try running as administrator (right-click → Run as administrator)"
    Write-Host ""
    Write-Host "Log file: $LOG_FILE" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
