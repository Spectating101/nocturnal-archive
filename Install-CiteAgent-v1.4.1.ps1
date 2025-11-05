# Cite-Agent Installer v1.4.1
# Self-contained, robust Windows installer
# Right-click → Run with PowerShell

#Requires -Version 5.1

param(
    [switch]$Silent,
    [switch]$NoShortcuts
)

# ============================================================================
# Configuration
# ============================================================================
$ErrorActionPreference = "Stop"
$CITE_AGENT_VERSION = "1.4.1"
$MIN_PYTHON_VERSION = [version]"3.10.0"
$MAX_PYTHON_VERSION = [version]"3.13.99"
$INSTALL_ROOT = "$env:LOCALAPPDATA\Cite-Agent"
$VENV_PATH = "$INSTALL_ROOT\venv"
$LOG_FILE = "$INSTALL_ROOT\logs\install-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# ============================================================================
# Logging Functions
# ============================================================================
function Initialize-Log {
    $logDir = Split-Path $LOG_FILE -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    "=== Cite-Agent Installation v$CITE_AGENT_VERSION ===" | Out-File $LOG_FILE -Encoding UTF8
    "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $LOG_FILE -Append -Encoding UTF8
    "Platform: $([Environment]::OSVersion.VersionString)" | Out-File $LOG_FILE -Append -Encoding UTF8
    "PowerShell: $($PSVersionTable.PSVersion)" | Out-File $LOG_FILE -Append -Encoding UTF8
    "" | Out-File $LOG_FILE -Append -Encoding UTF8
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "$timestamp | $Level | $Message" | Out-File $LOG_FILE -Append -Encoding UTF8

    switch ($Level) {
        "INFO"    { Write-Host "[*] $Message" -ForegroundColor Cyan }
        "SUCCESS" { Write-Host "[✓] $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "[!] $Message" -ForegroundColor Yellow }
        "ERROR"   { Write-Host "[✗] $Message" -ForegroundColor Red }
    }
}

# ============================================================================
# UI Functions
# ============================================================================
function Show-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                        ║" -ForegroundColor Cyan
    Write-Host "║   CITE-AGENT INSTALLER v$CITE_AGENT_VERSION                        ║" -ForegroundColor Cyan
    Write-Host "║   AI Research Assistant for Windows                    ║" -ForegroundColor Cyan
    Write-Host "║                                                        ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Progress {
    param(
        [string]$Activity,
        [int]$PercentComplete,
        [string]$Status
    )
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
}

# ============================================================================
# Python Detection
# ============================================================================
function Find-PythonExecutable {
    Write-Log "Searching for compatible Python installation..."

    # Strategy 1: Check py launcher (Windows Python Launcher)
    $pythonCandidates = @()

    try {
        $pyVersions = py -0 2>&1 | Select-String -Pattern '-(\d+\.\d+)-' | ForEach-Object {
            if ($_.Matches.Groups.Count -gt 1) {
                $version = $_.Matches.Groups[1].Value
                $fullPath = (py "-$version" -c "import sys; print(sys.executable)" 2>$null)
                if ($fullPath -and (Test-Path $fullPath)) {
                    [PSCustomObject]@{
                        Path = $fullPath
                        Version = [version]$version
                    }
                }
            }
        }
        $pythonCandidates += $pyVersions
        Write-Log "Found $($pyVersions.Count) Python version(s) via py launcher" -Level "INFO"
    } catch {
        Write-Log "py launcher not available" -Level "WARNING"
    }

    # Strategy 2: Check common installation paths
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
        "$env:ProgramFiles\Python3*\python.exe",
        "$env:ProgramFiles(x86)\Python3*\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python3*\python.exe"
    )

    foreach ($pathPattern in $commonPaths) {
        Get-Item $pathPattern -ErrorAction SilentlyContinue | ForEach-Object {
            $versionOutput = & $_.FullName --version 2>&1 | Select-String -Pattern '(\d+\.\d+\.\d+)'
            if ($versionOutput -and $versionOutput.Matches.Groups.Count -gt 1) {
                $version = [version]$versionOutput.Matches.Groups[1].Value
                $pythonCandidates += [PSCustomObject]@{
                    Path = $_.FullName
                    Version = $version
                }
            }
        }
    }

    # Strategy 3: Check PATH
    $pathPython = Get-Command python -ErrorAction SilentlyContinue
    if ($pathPython) {
        $versionOutput = & $pathPython.Path --version 2>&1 | Select-String -Pattern '(\d+\.\d+\.\d+)'
        if ($versionOutput -and $versionOutput.Matches.Groups.Count -gt 1) {
            $version = [version]$versionOutput.Matches.Groups[1].Value
            $pythonCandidates += [PSCustomObject]@{
                Path = $pathPython.Path
                Version = $version
            }
        }
    }

    # Filter for compatible versions and remove duplicates
    $compatiblePython = $pythonCandidates |
        Where-Object { $_.Version -ge $MIN_PYTHON_VERSION -and $_.Version -le $MAX_PYTHON_VERSION } |
        Sort-Object -Property @{Expression = {$_.Version}; Descending = $true} |
        Select-Object -First 1 -Unique

    if ($compatiblePython) {
        Write-Log "Selected Python: $($compatiblePython.Path) (v$($compatiblePython.Version))" -Level "SUCCESS"
        return $compatiblePython.Path
    }

    throw "No compatible Python found. Please install Python $MIN_PYTHON_VERSION to $MAX_PYTHON_VERSION from python.org"
}

# ============================================================================
# Virtual Environment
# ============================================================================
function New-VirtualEnvironment {
    param([string]$PythonPath)

    Write-Log "Creating virtual environment at: $VENV_PATH"
    Show-Progress -Activity "Installing Cite-Agent" -PercentComplete 20 -Status "Creating virtual environment..."

    # Remove old venv if exists
    if (Test-Path $VENV_PATH) {
        Write-Log "Removing existing virtual environment..." -Level "WARNING"
        Remove-Item $VENV_PATH -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Create fresh venv
    & $PythonPath -m venv $VENV_PATH 2>&1 | Out-File $LOG_FILE -Append -Encoding UTF8

    if (-not (Test-Path "$VENV_PATH\Scripts\python.exe")) {
        throw "Failed to create virtual environment"
    }

    Write-Log "Virtual environment created successfully" -Level "SUCCESS"
    return "$VENV_PATH\Scripts\python.exe"
}

# ============================================================================
# Package Installation
# ============================================================================
function Install-CiteAgent {
    param([string]$VenvPython)

    Write-Log "Upgrading pip, setuptools, wheel..."
    Show-Progress -Activity "Installing Cite-Agent" -PercentComplete 40 -Status "Upgrading pip..."

    # Upgrade pip first
    & $VenvPython -m pip install --upgrade pip setuptools wheel 2>&1 | Out-File $LOG_FILE -Append -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Warning: pip upgrade had issues (non-critical)" -Level "WARNING"
    }

    Write-Log "Installing cite-agent==$CITE_AGENT_VERSION from PyPI..."
    Show-Progress -Activity "Installing Cite-Agent" -PercentComplete 60 -Status "Downloading and installing cite-agent..."

    # Try installing from PyPI
    $installOutput = & $VenvPython -m pip install "cite-agent==$CITE_AGENT_VERSION" 2>&1
    $installOutput | Out-File $LOG_FILE -Append -Encoding UTF8

    if ($LASTEXITCODE -ne 0) {
        Write-Log "PyPI installation failed, trying without version pin..." -Level "WARNING"
        $installOutput = & $VenvPython -m pip install cite-agent 2>&1
        $installOutput | Out-File $LOG_FILE -Append -Encoding UTF8

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install cite-agent from PyPI"
        }
    }

    # Verify installation
    $verifyOutput = & $VenvPython -c "import cite_agent; print(cite_agent.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $installedVersion = $verifyOutput.Trim()
        Write-Log "cite-agent v$installedVersion installed successfully" -Level "SUCCESS"
    } else {
        throw "Installation verification failed"
    }
}

# ============================================================================
# Shortcuts
# ============================================================================
function New-Shortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$Arguments = "",
        [string]$WorkingDirectory = "",
        [string]$Description = ""
    )

    try {
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = $TargetPath
        $Shortcut.Arguments = $Arguments
        if ($WorkingDirectory) { $Shortcut.WorkingDirectory = $WorkingDirectory }
        if ($Description) { $Shortcut.Description = $Description }
        $Shortcut.Save()
        Write-Log "Created shortcut: $ShortcutPath" -Level "SUCCESS"
        return $true
    } catch {
        Write-Log "Failed to create shortcut: $($_.Exception.Message)" -Level "WARNING"
        return $false
    }
}

function Install-Shortcuts {
    if ($NoShortcuts) {
        Write-Log "Skipping shortcuts (--NoShortcuts flag)" -Level "INFO"
        return
    }

    Write-Log "Creating shortcuts..."
    Show-Progress -Activity "Installing Cite-Agent" -PercentComplete 80 -Status "Creating shortcuts..."

    $venvPython = "$VENV_PATH\Scripts\python.exe"
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"

    # Create launcher script
    $launcherScript = "$INSTALL_ROOT\launch-cite-agent.bat"
    @"
@echo off
cd /d "%USERPROFILE%"
"$venvPython" -m cite_agent.cli %*
"@ | Out-File $launcherScript -Encoding ASCII

    # Desktop shortcut
    $desktopShortcut = "$desktopPath\Cite-Agent.lnk"
    New-Shortcut -ShortcutPath $desktopShortcut -TargetPath $launcherScript -Description "Cite-Agent AI Research Assistant"

    # Start Menu shortcut
    $startMenuShortcut = "$startMenuPath\Cite-Agent.lnk"
    New-Shortcut -ShortcutPath $startMenuShortcut -TargetPath $launcherScript -Description "Cite-Agent AI Research Assistant"

    # Add to PATH (optional, user-level only)
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$INSTALL_ROOT*") {
        Write-Log "Adding $INSTALL_ROOT to user PATH..." -Level "INFO"
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$INSTALL_ROOT", "User")
    }
}

# ============================================================================
# Cleanup
# ============================================================================
function Remove-OldInstallations {
    Write-Log "Checking for old installations..."

    # Check for old venv
    if (Test-Path $VENV_PATH) {
        $answer = "Y"
        if (-not $Silent) {
            $answer = Read-Host "Existing installation found. Remove it? (Y/n)"
        }

        if ($answer -eq "" -or $answer -eq "Y" -or $answer -eq "y") {
            Write-Log "Removing old installation..." -Level "WARNING"
            Remove-Item $VENV_PATH -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# ============================================================================
# Main Installation
# ============================================================================
function Start-Installation {
    try {
        Show-Banner
        Initialize-Log

        Write-Log "=== Starting Cite-Agent Installation ===" -Level "INFO"
        Write-Log "Version: $CITE_AGENT_VERSION" -Level "INFO"
        Write-Log "Install location: $INSTALL_ROOT" -Level "INFO"
        Write-Host ""

        # Step 1: Find Python
        Show-Progress -Activity "Installing Cite-Agent" -PercentComplete 10 -Status "Detecting Python..."
        $pythonPath = Find-PythonExecutable

        # Step 2: Clean old installations
        Remove-OldInstallations

        # Step 3: Create venv
        $venvPython = New-VirtualEnvironment -PythonPath $pythonPath

        # Step 4: Install cite-agent
        Install-CiteAgent -VenvPython $venvPython

        # Step 5: Create shortcuts
        Install-Shortcuts

        # Complete
        Show-Progress -Activity "Installing Cite-Agent" -PercentComplete 100 -Status "Installation complete!"
        Write-Progress -Activity "Installing Cite-Agent" -Completed

        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                                                        ║" -ForegroundColor Green
        Write-Host "║   ✓ INSTALLATION SUCCESSFUL                            ║" -ForegroundColor Green
        Write-Host "║                                                        ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "Cite-Agent v$CITE_AGENT_VERSION is now installed!" -ForegroundColor Green
        Write-Host ""
        Write-Host "To start:" -ForegroundColor Cyan
        Write-Host "  • Double-click the 'Cite-Agent' icon on your desktop" -ForegroundColor White
        Write-Host "  • Or search for 'Cite-Agent' in the Start menu" -ForegroundColor White
        Write-Host "  • Or open PowerShell and run: cite-agent" -ForegroundColor White
        Write-Host ""
        Write-Host "Installation log: $LOG_FILE" -ForegroundColor Gray
        Write-Host ""

        if (-not $Silent) {
            $launch = Read-Host "Launch Cite-Agent now? (Y/n)"
            if ($launch -eq "" -or $launch -eq "Y" -or $launch -eq "y") {
                Write-Host ""
                Write-Host "Launching Cite-Agent..." -ForegroundColor Cyan
                Start-Process -FilePath "$VENV_PATH\Scripts\python.exe" -ArgumentList "-m","cite_agent.cli" -NoNewWindow
            }
        }

    } catch {
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Red
        Write-Host "║                                                        ║" -ForegroundColor Red
        Write-Host "║   ✗ INSTALLATION FAILED                                ║" -ForegroundColor Red
        Write-Host "║                                                        ║" -ForegroundColor Red
        Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Red
        Write-Host ""
        Write-Log "Installation failed: $($_.Exception.Message)" -Level "ERROR"
        Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
        Write-Host ""
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "  1. Ensure Python 3.10-3.13 is installed from python.org" -ForegroundColor White
        Write-Host "  2. Check your internet connection" -ForegroundColor White
        Write-Host "  3. Try running as administrator (right-click → Run as administrator)" -ForegroundColor White
        Write-Host "  4. Check the log file for details: $LOG_FILE" -ForegroundColor White
        Write-Host ""

        if (-not $Silent) {
            Read-Host "Press Enter to exit"
        }
        exit 1
    }
}

# ============================================================================
# Entry Point
# ============================================================================
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Start-Installation

if (-not $Silent) {
    Read-Host "`nPress Enter to exit"
}
