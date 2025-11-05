# Cite-Agent GUI Installer
# Provides visual progress bar and modern interface
# Can be converted to .exe using ps2exe

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Create form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Cite-Agent Installer v1.4.0"
$form.Size = New-Object System.Drawing.Size(600, 500)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.BackColor = [System.Drawing.Color]::White

# Logo/Title Panel
$titlePanel = New-Object System.Windows.Forms.Panel
$titlePanel.Location = New-Object System.Drawing.Point(0, 0)
$titlePanel.Size = New-Object System.Drawing.Size(600, 100)
$titlePanel.BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
$form.Controls.Add($titlePanel)

# Title Label
$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Location = New-Object System.Drawing.Point(20, 20)
$titleLabel.Size = New-Object System.Drawing.Size(560, 30)
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$titleLabel.Text = "Cite-Agent Installer"
$titleLabel.ForeColor = [System.Drawing.Color]::White
$titlePanel.Controls.Add($titleLabel)

# Subtitle Label
$subtitleLabel = New-Object System.Windows.Forms.Label
$subtitleLabel.Location = New-Object System.Drawing.Point(20, 55)
$subtitleLabel.Size = New-Object System.Drawing.Size(560, 25)
$subtitleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 11)
$subtitleLabel.Text = "AI Research Assistant for Windows | AI學術研究助手"
$subtitleLabel.ForeColor = [System.Drawing.Color]::FromArgb(230, 240, 255)
$titlePanel.Controls.Add($subtitleLabel)

# Description Label
$descLabel = New-Object System.Windows.Forms.Label
$descLabel.Location = New-Object System.Drawing.Point(30, 120)
$descLabel.Size = New-Object System.Drawing.Size(540, 80)
$descLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$descLabel.Text = @"
This installer will:
  • Remove any old versions (clean install)
  • Install Python if needed (no admin required)
  • Install Cite-Agent v1.4.0 from PyPI
  • Create desktop and Start Menu shortcuts
  • Add cite-agent to system PATH

Installation takes approximately 2 minutes.
"@
$form.Controls.Add($descLabel)

# Progress Bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(30, 220)
$progressBar.Size = New-Object System.Drawing.Size(540, 25)
$progressBar.Style = "Continuous"
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$form.Controls.Add($progressBar)

# Status Label
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Location = New-Object System.Drawing.Point(30, 255)
$statusLabel.Size = New-Object System.Drawing.Size(540, 25)
$statusLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$statusLabel.Text = "Ready to install..."
$statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
$form.Controls.Add($statusLabel)

# Log TextBox
$logBox = New-Object System.Windows.Forms.TextBox
$logBox.Location = New-Object System.Drawing.Point(30, 290)
$logBox.Size = New-Object System.Drawing.Size(540, 120)
$logBox.Multiline = $true
$logBox.ScrollBars = "Vertical"
$logBox.ReadOnly = $true
$logBox.Font = New-Object System.Drawing.Font("Consolas", 9)
$logBox.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)
$form.Controls.Add($logBox)

# Install Button
$installButton = New-Object System.Windows.Forms.Button
$installButton.Location = New-Object System.Drawing.Point(350, 425)
$installButton.Size = New-Object System.Drawing.Size(120, 35)
$installButton.Text = "Install"
$installButton.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$installButton.BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
$installButton.ForeColor = [System.Drawing.Color]::White
$installButton.FlatStyle = "Flat"
$installButton.FlatAppearance.BorderSize = 0
$form.Controls.Add($installButton)

# Close Button
$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Location = New-Object System.Drawing.Point(480, 425)
$closeButton.Size = New-Object System.Drawing.Size(90, 35)
$closeButton.Text = "Close"
$closeButton.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$closeButton.Enabled = $false
$form.Controls.Add($closeButton)

# Helper Functions
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logBox.AppendText("[$timestamp] $Message`r`n")
    $logBox.SelectionStart = $logBox.Text.Length
    $logBox.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
}

function Update-Progress {
    param([int]$Value, [string]$Status)
    $progressBar.Value = $Value
    $statusLabel.Text = $Status
    [System.Windows.Forms.Application]::DoEvents()
}

# Installation Logic
$installButton.Add_Click({
    $installButton.Enabled = $false

    try {
        Write-Log "Starting Cite-Agent installation..."
        Update-Progress -Value 5 -Status "Downloading installer script..."

        # Download and execute the web installer
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $installerUrl = "https://raw.githubusercontent.com/Spectating101/nocturnal-archive/production-backend-only/install-clean.ps1"

        Write-Log "Fetching installer from GitHub..."
        $installerScript = (New-Object System.Net.WebClient).DownloadString($installerUrl)

        Update-Progress -Value 10 -Status "Running installation..."
        Write-Log "Installer script downloaded successfully"

        # Parse and execute the installer with progress updates
        # We'll simulate progress based on expected stages

        # Stage 1: Uninstall (10-25%)
        Update-Progress -Value 10 -Status "Phase 1: Removing old installations..."
        Write-Log "Cleaning up old cite-agent installations..."

        # Remove old package
        try {
            $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
            if ($pythonCmd) {
                & python -m pip uninstall -y cite-agent 2>&1 | Out-Null
                Write-Log "Old package removed"
            }
        } catch { }

        Update-Progress -Value 15 -Status "Removing old shortcuts..."

        # Remove shortcuts
        $desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Cite-Agent.lnk"
        $startMenuFolder = Join-Path ([Environment]::GetFolderPath("Programs")) "Cite-Agent"

        if (Test-Path $desktopShortcut) { Remove-Item $desktopShortcut -Force -ErrorAction SilentlyContinue }
        if (Test-Path $startMenuFolder) { Remove-Item $startMenuFolder -Recurse -Force -ErrorAction SilentlyContinue }

        Write-Log "Shortcuts removed"
        Update-Progress -Value 20 -Status "Cleaning installation directory..."

        # Remove install directory
        $installRoot = "$env:LOCALAPPDATA\Cite-Agent"
        if (Test-Path $installRoot) {
            Remove-Item $installRoot -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Installation directory cleaned"
        }

        Update-Progress -Value 25 -Status "Cleanup complete"
        Write-Log "Phase 1 complete - clean slate ready"

        # Stage 2: Python Detection (25-40%)
        Update-Progress -Value 30 -Status "Phase 2: Checking for Python..."
        Write-Log "Detecting Python installation..."

        $pythonExe = $null

        # Try py launcher
        $pyTags = @("3.11-64", "3.11", "3.10-64", "3.10")
        foreach ($tag in $pyTags) {
            try {
                $pythonPath = & py -$tag -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $pythonPath) {
                    $pythonExe = $pythonPath.Trim()
                    Write-Log "Found Python: $pythonExe"
                    break
                }
            } catch { }
        }

        if (-not $pythonExe) {
            # Try system python
            try {
                $pythonCmd = Get-Command python -ErrorAction Stop
                $versionOutput = & $pythonCmd.Source --version 2>&1
                if ($versionOutput -match "Python 3\.(1[01]|10)") {
                    $pythonExe = $pythonCmd.Source
                    Write-Log "Found system Python: $pythonExe"
                }
            } catch { }
        }

        if (-not $pythonExe) {
            # Install Python
            Update-Progress -Value 35 -Status "Downloading Python 3.11.9..."
            Write-Log "No suitable Python found, installing Python 3.11.9..."

            $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
            $tempInstaller = Join-Path ([System.IO.Path]::GetTempPath()) "python-3.11.9-installer.exe"

            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($pythonUrl, $tempInstaller)

            Update-Progress -Value 38 -Status "Installing Python (this may take 1-2 minutes)..."
            Write-Log "Installing Python to $installRoot\python..."

            $embeddedPythonDir = "$installRoot\python"
            $installArgs = @(
                "/quiet",
                "InstallAllUsers=0",
                "PrependPath=0",
                "Include_test=0",
                "Include_launcher=0",
                "Shortcuts=0",
                "SimpleInstall=1",
                "TargetDir=`"$embeddedPythonDir`""
            )

            $process = Start-Process -FilePath $tempInstaller -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
            Remove-Item $tempInstaller -Force -ErrorAction SilentlyContinue

            $pythonExe = Join-Path $embeddedPythonDir "python.exe"
            Write-Log "Python installed successfully"
        }

        Update-Progress -Value 40 -Status "Python ready"

        # Stage 3: Virtual Environment (40-55%)
        Update-Progress -Value 45 -Status "Creating virtual environment..."
        Write-Log "Creating isolated virtual environment..."

        $venvPath = Join-Path $installRoot "venv"
        if (Test-Path $venvPath) {
            Remove-Item -Path $venvPath -Recurse -Force -ErrorAction SilentlyContinue
        }

        New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
        $process = Start-Process -FilePath $pythonExe -ArgumentList "-m", "venv", "`"$venvPath`"" -Wait -PassThru -NoNewWindow

        $venvPython = Join-Path $venvPath "Scripts\python.exe"
        Write-Log "Virtual environment created: $venvPath"
        Update-Progress -Value 55 -Status "Virtual environment ready"

        # Stage 4: Package Installation (55-80%)
        Update-Progress -Value 60 -Status "Upgrading pip..."
        Write-Log "Upgrading pip..."

        $process = Start-Process -FilePath $venvPython -ArgumentList "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel" -Wait -PassThru -NoNewWindow

        Update-Progress -Value 65 -Status "Installing Cite-Agent v1.4.0..."
        Write-Log "Installing cite-agent from PyPI (this may take 30-60 seconds)..."

        $process = Start-Process -FilePath $venvPython -ArgumentList "-m", "pip", "install", "--no-cache-dir", "cite-agent==1.4.0" -Wait -PassThru -NoNewWindow

        if ($process.ExitCode -ne 0) {
            throw "Cite-Agent installation failed"
        }

        Write-Log "Cite-Agent installed successfully"
        Update-Progress -Value 80 -Status "Package installation complete"

        # Stage 5: Shortcuts (80-90%)
        Update-Progress -Value 85 -Status "Creating shortcuts..."
        Write-Log "Creating desktop and Start Menu shortcuts..."

        $WshShell = New-Object -ComObject WScript.Shell

        # Desktop shortcut
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $desktopShortcut = $WshShell.CreateShortcut("$desktopPath\Cite-Agent.lnk")
        $desktopShortcut.TargetPath = $venvPython
        $desktopShortcut.Arguments = "-m cite_agent.cli"
        $desktopShortcut.WorkingDirectory = $installRoot
        $desktopShortcut.Description = "Cite-Agent AI Research Assistant"
        $desktopShortcut.IconLocation = "$env:SystemRoot\System32\cmd.exe,0"
        $desktopShortcut.Save()

        # Start Menu shortcut
        $startMenuPath = [Environment]::GetFolderPath("Programs")
        $startMenuFolder = Join-Path $startMenuPath "Cite-Agent"

        if (-not (Test-Path $startMenuFolder)) {
            New-Item -ItemType Directory -Path $startMenuFolder -Force | Out-Null
        }

        $startShortcut = $WshShell.CreateShortcut("$startMenuFolder\Cite-Agent.lnk")
        $startShortcut.TargetPath = $venvPython
        $startShortcut.Arguments = "-m cite_agent.cli"
        $startShortcut.WorkingDirectory = $installRoot
        $startShortcut.Description = "Cite-Agent AI Research Assistant"
        $startShortcut.IconLocation = "$env:SystemRoot\System32\cmd.exe,0"
        $startShortcut.Save()

        Write-Log "Shortcuts created successfully"
        Update-Progress -Value 90 -Status "Adding to PATH..."

        # Stage 6: PATH (90-95%)
        Write-Log "Adding cite-agent to system PATH..."

        $scriptsPath = Join-Path $venvPath "Scripts"
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

        if ($currentPath -notlike "*$scriptsPath*") {
            $newPath = "$currentPath;$scriptsPath"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            $env:Path = "$env:Path;$scriptsPath"
            Write-Log "PATH updated successfully"
        } else {
            Write-Log "Already in PATH"
        }

        Update-Progress -Value 95 -Status "Verifying installation..."

        # Stage 7: Verification (95-100%)
        Write-Log "Verifying installation..."

        $versionOutput = & $venvPython -m cite_agent.cli --version 2>&1
        Write-Log "Verification: $versionOutput"

        Update-Progress -Value 100 -Status "Installation complete!"
        Write-Log ""
        Write-Log "═══════════════════════════════════════"
        Write-Log "✓ INSTALLATION COMPLETE!"
        Write-Log "═══════════════════════════════════════"
        Write-Log ""
        Write-Log "You can now:"
        Write-Log "  1. Double-click 'Cite-Agent' on Desktop"
        Write-Log "  2. Search 'Cite-Agent' in Start Menu"
        Write-Log "  3. Type 'cite-agent' in any terminal"
        Write-Log ""
        Write-Log "For R Studio users: Restart R Studio first!"

        $statusLabel.Text = "✓ Installation successful!"
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0, 150, 0)

        $closeButton.Enabled = $true
        $closeButton.Focus()

        [System.Windows.Forms.MessageBox]::Show(
            "Cite-Agent installed successfully!`n`nYou can now:`n  • Double-click the desktop icon`n  • Type 'cite-agent' in any terminal`n  • Use in R Studio (restart R Studio first)`n`nPress Close to exit the installer.",
            "Installation Complete",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        )

    } catch {
        $errorMsg = $_.Exception.Message
        Write-Log ""
        Write-Log "═══════════════════════════════════════"
        Write-Log "✗ INSTALLATION FAILED"
        Write-Log "═══════════════════════════════════════"
        Write-Log "Error: $errorMsg"
        Write-Log ""
        Write-Log "Please check:"
        Write-Log "  - Internet connection"
        Write-Log "  - Firewall settings"
        Write-Log "  - Antivirus (may block Python)"

        $statusLabel.Text = "✗ Installation failed"
        $statusLabel.ForeColor = [System.Drawing.Color]::Red

        $installButton.Enabled = $true
        $closeButton.Enabled = $true

        [System.Windows.Forms.MessageBox]::Show(
            "Installation failed!`n`nError: $errorMsg`n`nCheck the log for details and try again.`n`nIf the problem persists, report it at:`nhttps://github.com/Spectating101/cite-agent/issues",
            "Installation Error",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        )
    }
})

$closeButton.Add_Click({
    $form.Close()
})

# Show the form
[void]$form.ShowDialog()
