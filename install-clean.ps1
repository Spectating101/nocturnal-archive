# Cite-Agent Clean Installer
# This script ALWAYS does a clean install: uninstall first, then fresh install
# Usage: iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install-clean.ps1 | iex

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Configuration
$PYTHON_VERSION = "3.11.9"
$PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
$INSTALL_ROOT = "$env:LOCALAPPDATA\Cite-Agent"
$LOG_FILE = "$INSTALL_ROOT\logs\install.log"

# Color output helpers (define first before use)
function Write-Status {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "[*] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor Red
}

# Auto-detect latest cite-agent version from PyPI
function Get-LatestCiteAgentVersion {
    try {
        $response = Invoke-RestMethod -Uri "https://pypi.org/pypi/cite-agent/json" -TimeoutSec 10
        return $response.info.version
    } catch {
        Write-Status "Failed to auto-detect version, using fallback: 1.3.9" -Color Yellow
        return "1.3.9"
    }
}

$CITE_AGENT_VERSION = Get-LatestCiteAgentVersion
Write-Status "Installing cite-agent version: $CITE_AGENT_VERSION" -Color Green

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "║   CITE-AGENT CLEAN INSTALLER                           ║" -ForegroundColor Cyan
Write-Host "║   Uninstalls old → Installs fresh                      ║" -ForegroundColor Cyan
Write-Host "║   Version $CITE_AGENT_VERSION                                         ║" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ========================================
# PHASE 1: UNINSTALL (Clean slate)
# ========================================

Write-Host "═══ PHASE 1: UNINSTALL OLD INSTALLATION ═══" -ForegroundColor Yellow
Write-Host ""

# 1. Remove from pip
Write-Status "Removing old cite-agent package..."
try {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        & python -m pip uninstall -y cite-agent 2>&1 | Out-Null
        Write-Success "Old package removed from pip"
    } else {
        Write-Status "No Python found, skipping pip uninstall"
    }
} catch {
    Write-Status "No old package found (this is fine)"
}

# 2. Remove desktop shortcut
Write-Status "Removing old shortcuts..."
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Cite-Agent.lnk"
if (Test-Path $desktopShortcut) {
    Remove-Item $desktopShortcut -Force -ErrorAction SilentlyContinue
    Write-Success "Desktop shortcut removed"
}

# 3. Remove Start Menu folder
$startMenuFolder = Join-Path ([Environment]::GetFolderPath("Programs")) "Cite-Agent"
if (Test-Path $startMenuFolder) {
    Remove-Item $startMenuFolder -Recurse -Force -ErrorAction SilentlyContinue
    Write-Success "Start Menu folder removed"
}

# 4. Remove old installation directory
Write-Status "Removing old installation files..."
if (Test-Path $INSTALL_ROOT) {
    Remove-Item $INSTALL_ROOT -Recurse -Force -ErrorAction SilentlyContinue
    Write-Success "Old installation directory removed"
}

# 5. Clean PATH
Write-Status "Cleaning PATH..."
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathsToRemove = @(
    "$env:LOCALAPPDATA\Cite-Agent\venv\Scripts",
    "$env:LOCALAPPDATA\Cite-Agent\python\Scripts"
)

$newPath = $currentPath
$pathCleaned = $false
foreach ($pathToRemove in $pathsToRemove) {
    if ($newPath -like "*$pathToRemove*") {
        $newPath = $newPath -replace [regex]::Escape(";$pathToRemove"), ""
        $newPath = $newPath -replace [regex]::Escape("$pathToRemove;"), ""
        $newPath = $newPath -replace [regex]::Escape("$pathToRemove"), ""
        $pathCleaned = $true
    }
}

if ($pathCleaned) {
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Success "PATH cleaned"
}

Write-Success "Uninstall complete - clean slate ready"
Write-Host ""
Start-Sleep -Seconds 1

# ========================================
# PHASE 2: FRESH INSTALL
# ========================================

Write-Host "═══ PHASE 2: FRESH INSTALLATION ═══" -ForegroundColor Yellow
Write-Host ""

# Logging
function Initialize-Log {
    $logDir = Split-Path $LOG_FILE -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    "=== Cite-Agent Clean Install - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Out-File $LOG_FILE -Encoding UTF8
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "$timestamp | $Message" | Out-File $LOG_FILE -Append -Encoding UTF8
}

Initialize-Log

# Python detection
function Get-ExistingPython {
    Write-Status "Checking for existing Python installation..."
    Write-Log "Searching for Python 3.10/3.11..."

    # Try py launcher first (check newer versions first)
    $pyTags = @("3.12-64", "3.12", "3.11-64", "3.11", "3.10-64", "3.10", "3.9-64", "3.9")
    foreach ($tag in $pyTags) {
        try {
            $pythonPath = & py -$tag -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $pythonPath) {
                Write-Success "Found Python via py launcher: $pythonPath"
                Write-Log "Detected Python: $pythonPath (py -$tag)"
                return $pythonPath.Trim()
            }
        } catch { }
    }

    # Try system python (accept 3.9+)
    try {
        $pythonCmd = Get-Command python -ErrorAction Stop
        $versionOutput = & $pythonCmd.Source --version 2>&1
        Write-Log "System python version: $versionOutput"

        if ($versionOutput -match "Python 3\.([9]|1[0-2])") {
            Write-Success "Found system Python: $($pythonCmd.Source)"
            return $pythonCmd.Source
        } else {
            Write-Log "Python version not supported: $versionOutput (need 3.9+)"
        }
    } catch {
        Write-Log "No system python found in PATH"
    }

    Write-Status "No suitable Python found, will install embedded version"
    Write-Log "Python detection failed, proceeding with embedded installation"
    return $null
}

# Download with progress
function Download-File {
    param([string]$Url, [string]$Destination)

    Write-Status "Downloading $(Split-Path $Url -Leaf)..."
    Write-Log "Downloading from: $Url"

    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $Destination)
        Write-Success "Download complete"
        Write-Log "Download successful: $Destination"
    } catch {
        Write-Error-Custom "Download failed: $_"
        Write-Log "Download error: $_"
        throw
    }
}

# Install embedded Python
function Install-EmbeddedPython {
    param([string]$TargetDir)

    Write-Status "Installing Python $PYTHON_VERSION (embedded)..."
    Write-Log "Installing Python to: $TargetDir"

    $tempInstaller = Join-Path ([System.IO.Path]::GetTempPath()) "python-$PYTHON_VERSION-installer.exe"

    Download-File -Url $PYTHON_DOWNLOAD_URL -Destination $tempInstaller

    Write-Status "Running Python installer (silent)..."
    Write-Log "Executing Python installer with silent flags"

    $installArgs = @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=0",
        "Include_test=0",
        "Include_launcher=0",
        "Shortcuts=0",
        "SimpleInstall=1",
        "TargetDir=`"$TargetDir`""
    )

    $process = Start-Process -FilePath $tempInstaller -ArgumentList $installArgs -Wait -PassThru -NoNewWindow

    if ($process.ExitCode -ne 0) {
        Write-Error-Custom "Python installation failed with exit code: $($process.ExitCode)"
        Write-Log "Python installer failed: exit code $($process.ExitCode)"
        throw "Python installation failed"
    }

    Remove-Item $tempInstaller -Force -ErrorAction SilentlyContinue

    $pythonExe = Join-Path $TargetDir "python.exe"
    if (-not (Test-Path $pythonExe)) {
        Write-Error-Custom "Python executable not found after installation"
        Write-Log "Python.exe not found at expected location: $pythonExe"
        throw "Python installation verification failed"
    }

    Write-Success "Python installed successfully"
    Write-Log "Python executable verified: $pythonExe"
    return $pythonExe
}

# Create virtual environment
function New-VirtualEnvironment {
    param([string]$PythonExe, [string]$VenvPath)

    Write-Status "Creating virtual environment..."
    Write-Log "Creating venv at: $VenvPath"

    if (Test-Path $VenvPath) {
        Remove-Item -Path $VenvPath -Recurse -Force -ErrorAction SilentlyContinue
    }

    $process = Start-Process -FilePath $PythonExe -ArgumentList "-m", "venv", "`"$VenvPath`"" -Wait -PassThru -NoNewWindow

    if ($process.ExitCode -ne 0) {
        Write-Error-Custom "Virtual environment creation failed"
        Write-Log "venv creation failed: exit code $($process.ExitCode)"
        throw "Virtual environment creation failed"
    }

    $venvPython = Join-Path $VenvPath "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Error-Custom "Virtual environment Python not found"
        Write-Log "venv python.exe not found: $venvPython"
        throw "Virtual environment verification failed"
    }

    Write-Success "Virtual environment created"
    Write-Log "Virtual environment ready: $venvPython"
    return $venvPython
}

# Install cite-agent
function Install-CiteAgent {
    param([string]$VenvPython, [string]$Version)

    Write-Status "Installing Cite-Agent v$Version..."
    Write-Log "Installing cite-agent==$Version via pip"

    # Upgrade pip first
    Write-Status "Upgrading pip..."
    $pipOutput = & $VenvPython -m pip install --upgrade pip setuptools wheel 2>&1
    Write-Log "Pip upgrade output: $pipOutput"

    if ($LASTEXITCODE -ne 0) {
        Write-Log "pip upgrade failed: exit code $LASTEXITCODE"
    }

    # Install cite-agent
    $installOutput = & $VenvPython -m pip install --no-cache-dir "cite-agent==$Version" 2>&1
    Write-Log "Pip install output: $installOutput"

    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Cite-Agent installation failed"
        Write-Log "pip install cite-agent failed: exit code $LASTEXITCODE"
        Write-Log "Full error: $installOutput"
        throw "Cite-Agent installation failed. Error: $installOutput"
    }

    Write-Success "Cite-Agent installed successfully"
    Write-Log "cite-agent installation complete"
}

# Create shortcuts
function New-Shortcuts {
    param([string]$VenvPython, [string]$InstallRoot)

    Write-Status "Creating shortcuts..."
    Write-Log "Creating desktop and start menu shortcuts"

    try {
        $WshShell = New-Object -ComObject WScript.Shell

        # Desktop shortcut
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "Cite-Agent.lnk"

        $desktopShortcut = $WshShell.CreateShortcut($shortcutPath)
        $desktopShortcut.TargetPath = "powershell.exe"
        $desktopShortcut.Arguments = "-NoExit -Command `"& '$VenvPython' -m cite_agent.cli`""
        $desktopShortcut.WorkingDirectory = $InstallRoot
        $desktopShortcut.Description = "Cite-Agent AI Research Assistant"
        $desktopShortcut.IconLocation = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe,0"
        $desktopShortcut.Save()
        Write-Log "Desktop shortcut created: $shortcutPath"

        # Start Menu shortcut
        $startMenuPath = [Environment]::GetFolderPath("Programs")
        $startMenuFolder = Join-Path $startMenuPath "Cite-Agent"

        if (-not (Test-Path $startMenuFolder)) {
            New-Item -ItemType Directory -Path $startMenuFolder -Force | Out-Null
        }

        $startShortcutPath = Join-Path $startMenuFolder "Cite-Agent.lnk"
        $startShortcut = $WshShell.CreateShortcut($startShortcutPath)
        $startShortcut.TargetPath = "powershell.exe"
        $startShortcut.Arguments = "-NoExit -Command `"& '$VenvPython' -m cite_agent.cli`""
        $startShortcut.WorkingDirectory = $InstallRoot
        $startShortcut.Description = "Cite-Agent AI Research Assistant"
        $startShortcut.IconLocation = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe,0"
        $startShortcut.Save()
        Write-Log "Start menu shortcut created: $startShortcutPath"

        Write-Success "Shortcuts created (Desktop + Start Menu)"
    } catch {
        Write-Status "Shortcut creation skipped (non-critical): $_" -Color Yellow
        Write-Log "Shortcut error (non-critical): $_"
    }
}

# Add to PATH
function Add-ToPath {
    param([string]$VenvPath)

    Write-Status "Adding cite-agent to PATH..."
    Write-Log "Adding Scripts directory to user PATH"

    $scriptsPath = Join-Path $VenvPath "Scripts"
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

    if ($currentPath -notlike "*$scriptsPath*") {
        $newPath = "$currentPath;$scriptsPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$env:Path;$scriptsPath"
        Write-Success "cite-agent added to PATH"
        Write-Log "PATH updated with: $scriptsPath"
    } else {
        Write-Success "cite-agent already in PATH"
        Write-Log "Scripts path already in PATH"
    }
}

# Verify installation
function Test-Installation {
    param([string]$VenvPython)

    Write-Status "Verifying installation..."
    Write-Log "Running cite-agent --version"

    try {
        $versionOutput = & $VenvPython -m cite_agent.cli --version 2>&1
        Write-Success "Cite-Agent is ready: $versionOutput"
        Write-Log "Verification successful: $versionOutput"
        return $true
    } catch {
        Write-Error-Custom "Verification failed: $_"
        Write-Log "Verification error: $_"
        return $false
    }
}

# Main installation flow
try {
    Write-Log "Installation started - Version: $CITE_AGENT_VERSION"

    # Create install directory
    if (-not (Test-Path $INSTALL_ROOT)) {
        New-Item -ItemType Directory -Path $INSTALL_ROOT -Force | Out-Null
        Write-Log "Created install directory: $INSTALL_ROOT"
    }

    # Detect or install Python
    $pythonExe = Get-ExistingPython

    if (-not $pythonExe) {
        $embeddedPythonDir = Join-Path $INSTALL_ROOT "python"
        $pythonExe = Install-EmbeddedPython -TargetDir $embeddedPythonDir
    }

    # Create virtual environment
    $venvPath = Join-Path $INSTALL_ROOT "venv"
    $venvPython = New-VirtualEnvironment -PythonExe $pythonExe -VenvPath $venvPath

    # Install cite-agent
    Install-CiteAgent -VenvPython $venvPython -Version $CITE_AGENT_VERSION

    # Create shortcuts
    New-Shortcuts -VenvPython $venvPython -InstallRoot $INSTALL_ROOT

    # Add to PATH
    Add-ToPath -VenvPath $venvPath

    # Verify
    $verified = Test-Installation -VenvPython $venvPython

    if ($verified) {
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                                                        ║" -ForegroundColor Green
        Write-Host "║   ✓ CLEAN INSTALLATION COMPLETE!                       ║" -ForegroundColor Green
        Write-Host "║                                                        ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "🚀 Starting Cite-Agent..." -ForegroundColor Yellow
        Write-Host ""
        Write-Log "Installation completed successfully"

        # Launch cite-agent directly for immediate testing
        $citeAgentExe = Join-Path $venvPath "Scripts\cite-agent.exe"
        if (Test-Path $citeAgentExe) {
            & $citeAgentExe
        } else {
            # Fallback: run via python module
            & $venvPython -m cite_agent.cli
        }
    } else {
        throw "Installation verification failed"
    }

} catch {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                                                        ║" -ForegroundColor Red
    Write-Host "║   ✗ INSTALLATION FAILED                                ║" -ForegroundColor Red
    Write-Host "║                                                        ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 Check log file: $LOG_FILE" -ForegroundColor Yellow
    Write-Host "🐛 Report issues: https://github.com/Spectating101/cite-agent/issues" -ForegroundColor Yellow
    Write-Host ""
    Write-Log "Installation failed: $_"
    exit 1
}
