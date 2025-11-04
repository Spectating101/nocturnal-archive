# Cite-Agent One-Line Installer
# Usage: iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex
# Or: irm https://raw.githubusercontent.com/Spectating101/cite-agent/main/install.ps1 | iex

<#
.SYNOPSIS
    Installs Cite-Agent for Windows users with zero dependencies.

.DESCRIPTION
    This script performs a fully automated installation:
    1. Detects or installs Python 3.11 (embedded, no admin rights needed)
    2. Creates isolated virtual environment in %LOCALAPPDATA%\Cite-Agent
    3. Installs cite-agent from PyPI
    4. Creates desktop + start menu shortcuts
    5. Adds cite-agent to PATH (persistent)

.NOTES
    - No admin rights required
    - Works on Windows 10/11
    - Safe to re-run (idempotent)
    - Bilingual support (English/Chinese)
#>

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Configuration
$CITE_AGENT_VERSION = "1.4.0"
$PYTHON_VERSION = "3.11.9"
$PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
$INSTALL_ROOT = "$env:LOCALAPPDATA\Cite-Agent"
$LOG_FILE = "$INSTALL_ROOT\logs\install.log"

# Color output helpers
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

# Logging
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
}

# Python detection
function Get-ExistingPython {
    Write-Status "Checking for existing Python installation..."
    Write-Log "Searching for Python 3.10/3.11..."

    # Try py launcher first (most reliable on Windows)
    $pyTags = @("3.11-64", "3.11", "3.10-64", "3.10")
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

    # Try system python command
    try {
        $pythonCmd = Get-Command python -ErrorAction Stop
        $versionOutput = & $pythonCmd.Source --version 2>&1
        Write-Log "System python version: $versionOutput"

        if ($versionOutput -match "Python 3\.(1[01]|10)") {
            Write-Success "Found system Python: $($pythonCmd.Source)"
            return $pythonCmd.Source
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
    param(
        [string]$Url,
        [string]$Destination
    )

    Write-Status "Downloading $(Split-Path $Url -Leaf)..."
    Write-Log "Downloading from: $Url"
    Write-Log "Saving to: $Destination"

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
    param(
        [string]$PythonExe,
        [string]$VenvPath
    )

    Write-Status "Creating virtual environment..."
    Write-Log "Creating venv at: $VenvPath"

    if (Test-Path $VenvPath) {
        Write-Status "Removing existing virtual environment..."
        Write-Log "Cleaning up old venv"
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
    param(
        [string]$VenvPython,
        [string]$Version
    )

    Write-Status "Installing Cite-Agent v$Version..."
    Write-Log "Installing cite-agent==$Version via pip"

    # Upgrade pip first
    Write-Status "Upgrading pip..."
    $process = Start-Process -FilePath $VenvPython -ArgumentList "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel" -Wait -PassThru -NoNewWindow

    if ($process.ExitCode -ne 0) {
        Write-Error-Custom "pip upgrade failed"
        Write-Log "pip upgrade failed: exit code $($process.ExitCode)"
    }

    # Install cite-agent
    $process = Start-Process -FilePath $VenvPython -ArgumentList "-m", "pip", "install", "--no-cache-dir", "cite-agent==$Version" -Wait -PassThru -NoNewWindow

    if ($process.ExitCode -ne 0) {
        Write-Error-Custom "Cite-Agent installation failed"
        Write-Log "pip install cite-agent failed: exit code $($process.ExitCode)"
        throw "Cite-Agent installation failed"
    }

    Write-Success "Cite-Agent installed successfully"
    Write-Log "cite-agent installation complete"
}

# Create shortcuts
function New-Shortcuts {
    param(
        [string]$VenvPython,
        [string]$InstallRoot
    )

    Write-Status "Creating shortcuts..."
    Write-Log "Creating desktop and start menu shortcuts"

    $WshShell = New-Object -ComObject WScript.Shell

    # Desktop shortcut
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $desktopShortcut = $WshShell.CreateShortcut("$desktopPath\Cite-Agent.lnk")
    $desktopShortcut.TargetPath = $VenvPython
    $desktopShortcut.Arguments = "-m cite_agent.cli"
    $desktopShortcut.WorkingDirectory = $InstallRoot
    $desktopShortcut.Description = "Cite-Agent AI Research Assistant"
    $desktopShortcut.IconLocation = "$env:SystemRoot\System32\cmd.exe,0"
    $desktopShortcut.Save()
    Write-Log "Desktop shortcut created: $desktopPath\Cite-Agent.lnk"

    # Start Menu shortcut
    $startMenuPath = [Environment]::GetFolderPath("Programs")
    $startMenuFolder = Join-Path $startMenuPath "Cite-Agent"

    if (-not (Test-Path $startMenuFolder)) {
        New-Item -ItemType Directory -Path $startMenuFolder -Force | Out-Null
    }

    $startShortcut = $WshShell.CreateShortcut("$startMenuFolder\Cite-Agent.lnk")
    $startShortcut.TargetPath = $VenvPython
    $startShortcut.Arguments = "-m cite_agent.cli"
    $startShortcut.WorkingDirectory = $InstallRoot
    $startShortcut.Description = "Cite-Agent AI Research Assistant"
    $startShortcut.IconLocation = "$env:SystemRoot\System32\cmd.exe,0"
    $startShortcut.Save()
    Write-Log "Start menu shortcut created: $startMenuFolder\Cite-Agent.lnk"

    Write-Success "Shortcuts created (Desktop + Start Menu)"
}

# Add to PATH
function Add-ToPath {
    param([string]$VenvPath)

    Write-Status "Adding cite-agent to PATH..."
    Write-Log "Adding Scripts directory to user PATH"

    $scriptsPath = Join-Path $VenvPath "Scripts"

    # Get current user PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

    if ($currentPath -notlike "*$scriptsPath*") {
        $newPath = "$currentPath;$scriptsPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")

        # Update current session PATH
        $env:Path = "$env:Path;$scriptsPath"

        Write-Success "cite-agent added to PATH"
        Write-Log "PATH updated with: $scriptsPath"
    } else {
        Write-Success "cite-agent already in PATH"
        Write-Log "Scripts path already in PATH"
    }
}

# Create launcher batch file
function New-LauncherBatch {
    param([string]$VenvPython, [string]$InstallRoot)

    $batchPath = Join-Path $InstallRoot "cite-agent.bat"

    $batchContent = @"
@echo off
REM Cite-Agent Launcher
REM Auto-generated by installer

cd /d "%LOCALAPPDATA%\Cite-Agent"
"$VenvPython" -m cite_agent.cli %*
"@

    $batchContent | Out-File -FilePath $batchPath -Encoding ASCII -Force
    Write-Log "Launcher batch created: $batchPath"
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
function Install-Main {
    try {
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                                                        ║" -ForegroundColor Cyan
        Write-Host "║   CITE-AGENT INSTALLER                                 ║" -ForegroundColor Cyan
        Write-Host "║   AI Research Assistant for Windows                    ║" -ForegroundColor Cyan
        Write-Host "║   Version $CITE_AGENT_VERSION                                         ║" -ForegroundColor Cyan
        Write-Host "║                                                        ║" -ForegroundColor Cyan
        Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""

        Initialize-Log
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

        # Create launcher
        New-LauncherBatch -VenvPython $venvPython -InstallRoot $INSTALL_ROOT

        # Verify
        $verified = Test-Installation -VenvPython $venvPython

        if ($verified) {
            Write-Host ""
            Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
            Write-Host "║                                                        ║" -ForegroundColor Green
            Write-Host "║   ✓ INSTALLATION COMPLETE!                             ║" -ForegroundColor Green
            Write-Host "║                                                        ║" -ForegroundColor Green
            Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
            Write-Host ""
            Write-Host "🚀 Quick Start:" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "   1. Double-click 'Cite-Agent' on your Desktop" -ForegroundColor White
            Write-Host "   2. Or search 'Cite-Agent' in Start Menu" -ForegroundColor White
            Write-Host "   3. Or type 'cite-agent' in any terminal" -ForegroundColor White
            Write-Host ""
            Write-Host "📚 Features:" -ForegroundColor Yellow
            Write-Host "   • Search 200M+ research papers" -ForegroundColor White
            Write-Host "   • Get citations in any format" -ForegroundColor White
            Write-Host "   • Real-time financial data" -ForegroundColor White
            Write-Host "   • AI research assistant" -ForegroundColor White
            Write-Host ""
            Write-Host "📝 Installation log: $LOG_FILE" -ForegroundColor Gray
            Write-Host ""
            Write-Log "Installation completed successfully"
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
}

# Run installation
Install-Main
