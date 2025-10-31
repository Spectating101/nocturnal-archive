# ========================================
# Cite-Agent Professional Installer v2.0
# PowerShell GUI Installer with Progress Bar
# Bilingual Support: English / 中文
# ========================================

param(
    [string]$DefaultVersion = "1.3.9",
    [string]$PythonVersion = "3.11.9",
    [string]$PythonDownloadUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe",
    [switch]$LaunchFromInstaller
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

if (-not $LaunchFromInstaller.IsPresent) {
    [System.Windows.Forms.MessageBox]::Show(
        "Please run the official Cite-Agent Installer (.exe) instead of launching Install-CiteAgent.ps1 directly." + `
        "`n`nDownload or rebuild `Cite-Agent-Installer-v2.0.exe` and double-click that file.",
        "Cite-Agent Installer",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
    exit 1
}

# ========================================
# GUI Setup
# ========================================

$form = New-Object System.Windows.Forms.Form
$form.Text = "Cite-Agent Installer v2.0 安裝程式"
$form.Size = New-Object System.Drawing.Size(600,450)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false

# Title Label
$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Location = New-Object System.Drawing.Point(20,20)
$titleLabel.Size = New-Object System.Drawing.Size(560,40)
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI",16,[System.Drawing.FontStyle]::Bold)
$titleLabel.Text = "Cite-Agent Installer"
$titleLabel.TextAlign = "MiddleCenter"
$form.Controls.Add($titleLabel)

# Subtitle Label (Bilingual)
$subtitleLabel = New-Object System.Windows.Forms.Label
$subtitleLabel.Location = New-Object System.Drawing.Point(20,65)
$subtitleLabel.Size = New-Object System.Drawing.Size(560,25)
$subtitleLabel.Font = New-Object System.Drawing.Font("Segoe UI",10)
$subtitleLabel.Text = "AI Research Assistant for Academics | AI學術研究助手"
$subtitleLabel.TextAlign = "MiddleCenter"
$subtitleLabel.ForeColor = [System.Drawing.Color]::Gray
$form.Controls.Add($subtitleLabel)

# Progress Bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(20,110)
$progressBar.Size = New-Object System.Drawing.Size(560,30)
$progressBar.Style = "Continuous"
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$form.Controls.Add($progressBar)

# Status Label
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Location = New-Object System.Drawing.Point(20,150)
$statusLabel.Size = New-Object System.Drawing.Size(560,25)
$statusLabel.Font = New-Object System.Drawing.Font("Segoe UI",10)
$statusLabel.Text = "Ready to install... / 準備安裝..."
$form.Controls.Add($statusLabel)

# Log TextBox
$logBox = New-Object System.Windows.Forms.TextBox
$logBox.Location = New-Object System.Drawing.Point(20,185)
$logBox.Size = New-Object System.Drawing.Size(560,180)
$logBox.Multiline = $true
$logBox.ScrollBars = "Vertical"
$logBox.ReadOnly = $true
$logBox.Font = New-Object System.Drawing.Font("Consolas",9)
$form.Controls.Add($logBox)

# Install Button
$installButton = New-Object System.Windows.Forms.Button
$installButton.Location = New-Object System.Drawing.Point(350,375)
$installButton.Size = New-Object System.Drawing.Size(120,35)
$installButton.Text = "Install 安裝"
$installButton.Font = New-Object System.Drawing.Font("Segoe UI",10,[System.Drawing.FontStyle]::Bold)
$installButton.BackColor = [System.Drawing.Color]::FromArgb(0,120,215)
$installButton.ForeColor = [System.Drawing.Color]::White
$installButton.FlatStyle = "Flat"
$form.Controls.Add($installButton)

# Close Button
$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Location = New-Object System.Drawing.Point(480,375)
$closeButton.Size = New-Object System.Drawing.Size(100,35)
$closeButton.Text = "Close 關閉"
$closeButton.Font = New-Object System.Drawing.Font("Segoe UI",10)
$closeButton.Enabled = $false
$form.Controls.Add($closeButton)

# ========================================
# Helper Functions
# ========================================

function Write-Log {
    param([string]$Message)
    $logBox.AppendText("$Message`r`n")
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

# ========================================
# Installation Logic
# ========================================

$installButton.Add_Click({
    $installButton.Enabled = $false

    try {
        # Step 1: Check Python (14%)
        Update-Progress -Value 0 -Status "Checking Python... / 檢查 Python..."
        Write-Log "[1/7] Checking for Python... / 檢查 Python..."

        $pythonCheck = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCheck) {
            Write-Log "Python not found. Installing Python $PythonVersion... / 未找到 Python，正在安裝..."
            Update-Progress -Value 5 -Status "Downloading Python... / 下載 Python..."

            $pythonInstaller = Join-Path $env:TEMP "python-$PythonVersion-installer.exe"

            Invoke-WebRequest -Uri $PythonDownloadUrl -OutFile $pythonInstaller -UseBasicParsing

            Update-Progress -Value 10 -Status "Installing Python... / 安裝 Python..."
            Write-Log "Installing Python (this may take 1-2 minutes)... / 安裝中 (需要1-2分鐘)..."

            Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet","InstallAllUsers=1","PrependPath=1" -Wait
            Remove-Item $pythonInstaller -Force

            Write-Log "[OK] Python installed / Python 已安裝"
            Start-Sleep -Seconds 2
        } else {
            Write-Log "[OK] Python found: $(python --version) / 已找到 Python"
        }

        Update-Progress -Value 14 -Status "Python ready / Python 準備就緒"

        # Step 2: Get latest version from PyPI (28%)
        Update-Progress -Value 14 -Status "Checking latest version... / 檢查最新版本..."
        Write-Log "[2/7] Fetching latest cite-agent version from PyPI... / 從 PyPI 獲取最新版本..."

        try {
            $pypiUrl = "https://pypi.org/pypi/cite-agent/json"
            $pypiData = Invoke-RestMethod -Uri $pypiUrl
            $version = $pypiData.info.version
            Write-Log "[OK] Latest version: $version / 最新版本: $version"
        } catch {
            $version = $DefaultVersion
            Write-Log "[WARNING] Could not fetch version, using default: $version / 使用預設版本"
        }

        Update-Progress -Value 28 -Status "Version: $version"

        # Step 3: Verify Python & pip (42%)
        Update-Progress -Value 28 -Status "Verifying Python... / 驗證 Python..."
        Write-Log "[3/7] Verifying Python installation... / 驗證 Python 安裝..."

        $pipCheck = python -m pip --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "pip not found. Python installation incomplete. / pip 未找到，Python 安裝不完整"
        }
        Write-Log "[OK] pip ready / pip 準備就緒"

        Update-Progress -Value 42 -Status "Python verified / Python 已驗證"

        # Step 4: Remove old version (56%)
        Update-Progress -Value 42 -Status "Checking for old version... / 檢查舊版本..."
        Write-Log "[4/7] Checking for old cite-agent... / 檢查舊版 cite-agent..."

        $oldVersion = python -m pip show cite-agent 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Removing old version... / 移除舊版本..."
            python -m pip uninstall -y cite-agent | Out-Null
            Write-Log "[OK] Old version removed / 已移除舊版本"
        } else {
            Write-Log "[OK] No old version found / 未找到舊版本"
        }

        Update-Progress -Value 56 -Status "Ready to install / 準備安裝"

        # Step 5: Install cite-agent (70%)
        Update-Progress -Value 56 -Status "Installing cite-agent... / 安裝 cite-agent..."
        Write-Log "[5/7] Installing cite-agent v$version... / 安裝 cite-agent v$version..."
        Write-Log "(This may take 30-60 seconds) / (需要 30-60 秒)"

        python -m pip install --user --no-cache-dir "cite-agent==$version" 2>&1 | ForEach-Object {
            if ($_ -match "Successfully installed") {
                Write-Log $_
            }
        }

        if ($LASTEXITCODE -ne 0) {
            throw "Installation failed / 安裝失敗"
        }

        Write-Log "[OK] cite-agent installed / cite-agent 已安裝"
        Update-Progress -Value 70 -Status "cite-agent installed / 已安裝"

        # Step 6: Add to PATH & broadcast change (85%)
        Update-Progress -Value 70 -Status "Adding to PATH... / 添加到系統路徑..."
        Write-Log "[6/7] Adding cite-agent to system PATH... / 添加到系統路徑..."

        $scriptsPath = python -c "import site; print(site.USER_BASE + '\\Scripts')"
        Write-Log "Scripts path: $scriptsPath"

        $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        if ($userPath -notlike "*$scriptsPath*") {
            [Environment]::SetEnvironmentVariable('Path', "$userPath;$scriptsPath", 'User')
            Write-Log "[OK] Added to PATH / 已添加到路徑"

            # Broadcast environment change
            Write-Log "Broadcasting PATH change to Windows... / 廣播路徑更改..."
            $HWND_BROADCAST = [IntPtr]0xffff
            $WM_SETTINGCHANGE = 0x1a
            Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition @"
                [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
                public static extern IntPtr SendMessageTimeout(
                    IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
                    uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
            $result = [UIntPtr]::Zero
            [Win32.NativeMethods]::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, "Environment", 2, 5000, [ref]$result) | Out-Null
            Write-Log "[OK] PATH broadcast complete / 路徑廣播完成"
        } else {
            Write-Log "[OK] Already in PATH / 已在路徑中"
        }

        Update-Progress -Value 85 -Status "PATH updated / 路徑已更新"

        # Step 7: Create shortcuts (100%)
        Update-Progress -Value 85 -Status "Creating shortcuts... / 創建快捷方式..."
        Write-Log "[7/7] Creating desktop and Start Menu shortcuts... / 創建桌面和開始菜單快捷方式..."

        $WshShell = New-Object -ComObject WScript.Shell

        # Desktop shortcut
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcut = $WshShell.CreateShortcut("$desktopPath\Cite-Agent.lnk")
        $shortcut.TargetPath = "cmd.exe"
        $shortcut.Arguments = "/k python -m cite_agent.cli"
        $shortcut.WorkingDirectory = $desktopPath
        $shortcut.Description = "Cite-Agent AI Research Assistant"
        $shortcut.Save()
        Write-Log "[OK] Desktop shortcut created / 桌面快捷方式已創建"

        # Start Menu shortcut
        $startMenuPath = [Environment]::GetFolderPath("Programs")
        $shortcut = $WshShell.CreateShortcut("$startMenuPath\Cite-Agent.lnk")
        $shortcut.TargetPath = "cmd.exe"
        $shortcut.Arguments = "/k python -m cite_agent.cli"
        $shortcut.WorkingDirectory = $desktopPath
        $shortcut.Description = "Cite-Agent AI Research Assistant"
        $shortcut.Save()
        Write-Log "[OK] Start Menu shortcut created / 開始菜單快捷方式已創建"

        Update-Progress -Value 100 -Status "Installation complete! / 安裝完成！"

        # Show completion message
        Write-Log ""
        Write-Log "========================================"
        Write-Log "  INSTALLATION COMPLETE! / 安裝完成！"
        Write-Log "========================================"
        Write-Log ""
        $versionOutput = python -m cite_agent.cli --version 2>&1
        Write-Log $versionOutput
        Write-Log ""
        Write-Log "HOW TO USE / 使用方法:"
        Write-Log "-------------------"
        Write-Log "1. Double-click 'Cite-Agent' icon on Desktop"
        Write-Log "   雙擊桌面上的 'Cite-Agent' 圖標"
        Write-Log ""
        Write-Log "2. Or open Start Menu and search 'Cite-Agent'"
        Write-Log "   或打開開始菜單搜索 'Cite-Agent'"
        Write-Log ""
        Write-Log "3. For R Studio / Stata users:"
        Write-Log "   R Studio / Stata 用戶:"
        Write-Log "   - Open Terminal pane / 打開終端窗格"
        Write-Log "   - Type: cite-agent / 輸入: cite-agent"
        Write-Log "   - Press Enter / 按回車"
        Write-Log ""
        Write-Log "IMPORTANT / 重要提示:"
        Write-Log "If R Studio is currently open, close and reopen it."
        Write-Log "如果 R Studio 當前正在運行，請關閉並重新打開。"
        Write-Log ""
        Write-Log "========================================"

        $closeButton.Enabled = $true
        $closeButton.Focus()

        [System.Windows.Forms.MessageBox]::Show(
            "Installation completed successfully!`n安裝成功完成！`n`nYou can now close this window and launch Cite-Agent from your Desktop.`n您現在可以關閉此窗口並從桌面啟動 Cite-Agent。",
            "Success / 成功",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        )

    } catch {
        Write-Log ""
        Write-Log "[ERROR] Installation failed / 安裝失敗: $_"
        Write-Log ""
        Update-Progress -Value 0 -Status "Installation failed / 安裝失敗"

        [System.Windows.Forms.MessageBox]::Show(
            "Installation failed. Please check the log for details.`n安裝失敗。請查看日誌了解詳情。`n`nError: $_",
            "Error / 錯誤",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        )

        $installButton.Enabled = $true
        $closeButton.Enabled = $true
    }
})

$closeButton.Add_Click({
    $form.Close()
})

# Show the form
[void]$form.ShowDialog()
