# Cite-Agent Uninstaller
# Removes cite-agent and cleans up corrupted installations
# Usage: iwr -useb https://raw.githubusercontent.com/Spectating101/cite-agent/main/uninstall.ps1 | iex

$ErrorActionPreference = "Stop"

function Write-Status {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor Green
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║                                                        ║" -ForegroundColor Red
Write-Host "║   CITE-AGENT UNINSTALLER                               ║" -ForegroundColor Red
Write-Host "║   Removes cite-agent and cleans corrupted installs     ║" -ForegroundColor Red
Write-Host "║                                                        ║" -ForegroundColor Red
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

# Confirm uninstall
$confirm = Read-Host "This will remove Cite-Agent from your system. Continue? (y/N)"
if ($confirm -ne "y") {
    Write-Host "Uninstall cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Status "Starting uninstall..."

# 1. Remove from pip
Write-Status "Removing cite-agent package..."
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
    & python -m pip uninstall -y cite-agent 2>&1 | Out-Null
    Write-Success "Package removed from pip"
} catch {
    Write-Host "[!] Python/pip not found, skipping package removal" -ForegroundColor Yellow
}

# 2. Remove desktop shortcut
Write-Status "Removing desktop shortcut..."
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Cite-Agent.lnk"
if (Test-Path $desktopShortcut) {
    Remove-Item $desktopShortcut -Force
    Write-Success "Desktop shortcut removed"
}

# 3. Remove Start Menu folder
Write-Status "Removing Start Menu shortcuts..."
$startMenuFolder = Join-Path ([Environment]::GetFolderPath("Programs")) "Cite-Agent"
if (Test-Path $startMenuFolder) {
    Remove-Item $startMenuFolder -Recurse -Force
    Write-Success "Start Menu folder removed"
}

# 4. Remove installation directory
Write-Status "Removing installation files..."
$installRoot = "$env:LOCALAPPDATA\Cite-Agent"
if (Test-Path $installRoot) {
    Remove-Item $installRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Success "Installation directory removed: $installRoot"
}

# 5. Clean PATH
Write-Status "Cleaning PATH..."
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathsToRemove = @(
    "$env:LOCALAPPDATA\Cite-Agent\venv\Scripts",
    "$env:LOCALAPPDATA\Cite-Agent\python\Scripts"
)

$newPath = $currentPath
foreach ($pathToRemove in $pathsToRemove) {
    if ($newPath -like "*$pathToRemove*") {
        $newPath = $newPath -replace [regex]::Escape(";$pathToRemove"), ""
        $newPath = $newPath -replace [regex]::Escape("$pathToRemove;"), ""
        $newPath = $newPath -replace [regex]::Escape("$pathToRemove"), ""
    }
}

if ($newPath -ne $currentPath) {
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Success "PATH cleaned"
} else {
    Write-Host "[!] cite-agent not found in PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                        ║" -ForegroundColor Green
Write-Host "║   ✓ UNINSTALL COMPLETE                                 ║" -ForegroundColor Green
Write-Host "║                                                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Cite-Agent has been removed from your system." -ForegroundColor White
Write-Host ""
Write-Host "Note: Restart your terminal or computer for PATH changes to take effect." -ForegroundColor Yellow
Write-Host ""
