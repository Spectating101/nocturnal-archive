# PowerShell Setup Script for OpenInterpreter + Groq
# R/SQL AI Assistant Setup for Students

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  R/SQL AI Assistant Setup for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if pip is available
try {
    $pipVersion = pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] pip found" -ForegroundColor Green
    } else {
        throw "pip not found"
    }
} catch {
    Write-Host "[ERROR] pip is not available" -ForegroundColor Red
    Write-Host "Please reinstall Python with pip included" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Create virtual environment
Write-Host "[STEP 1] Creating virtual environment..." -ForegroundColor Yellow
try {
    python -m venv r_sql_assistant_env
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    } else {
        throw "Failed to create virtual environment"
    }
} catch {
    Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "[STEP 2] Activating virtual environment..." -ForegroundColor Yellow
try {
    & ".\r_sql_assistant_env\Scripts\Activate.ps1"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    } else {
        throw "Failed to activate virtual environment"
    }
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Upgrade pip
Write-Host "[STEP 3] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "[OK] pip upgraded" -ForegroundColor Green

# Install OpenInterpreter
Write-Host "[STEP 4] Installing OpenInterpreter..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Cyan
try {
    pip install open-interpreter
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] OpenInterpreter installed" -ForegroundColor Green
    } else {
        throw "Failed to install OpenInterpreter"
    }
} catch {
    Write-Host "[ERROR] Failed to install OpenInterpreter" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Try installing with --no-deps flag:" -ForegroundColor Yellow
    Write-Host "pip install open-interpreter --no-deps" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Create startup script
Write-Host "[STEP 5] Creating startup script..." -ForegroundColor Yellow
$startupScript = @"
@echo off
REM R/SQL AI Assistant Startup Script
echo Starting R/SQL AI Assistant with Groq...
echo.
echo Make sure you have set your GROQ_API_KEY:
echo set GROQ_API_KEY=your-key-here
echo.
call r_sql_assistant_env\Scripts\activate.bat
interpreter --model groq/llama-3.1-70b-versatile
pause
"@

$startupScript | Out-File -FilePath "start_assistant.bat" -Encoding ASCII
Write-Host "[OK] Startup script created: start_assistant.bat" -ForegroundColor Green

# Create API key setup script
Write-Host "[STEP 6] Creating API key setup script..." -ForegroundColor Yellow
$apiKeyScript = @"
@echo off
REM Set your Groq API Key
echo Setting up Groq API Key...
echo.
set /p api_key="Enter your Groq API Key: "
setx GROQ_API_KEY "%api_key%"
echo.
echo API Key set successfully!
echo You may need to restart your terminal for changes to take effect.
echo.
pause
"@

$apiKeyScript | Out-File -FilePath "setup_api_key.bat" -Encoding ASCII
Write-Host "[OK] API key setup script created: setup_api_key.bat" -ForegroundColor Green

# Create PowerShell startup script
$psStartupScript = @"
# PowerShell Startup Script for R/SQL AI Assistant
Write-Host "Starting R/SQL AI Assistant with Groq..." -ForegroundColor Cyan
Write-Host ""

# Check if API key is set
if (-not $env:GROQ_API_KEY) {
    Write-Host "[WARNING] GROQ_API_KEY is not set!" -ForegroundColor Yellow
    Write-Host "Please run: setup_api_key.bat" -ForegroundColor Yellow
    Write-Host "Or set it manually: `$env:GROQ_API_KEY = 'your-key-here'" -ForegroundColor Yellow
    Write-Host ""
}

# Activate virtual environment and start interpreter
& ".\r_sql_assistant_env\Scripts\Activate.ps1"
interpreter --model groq/llama-3.1-70b-versatile
"@

$psStartupScript | Out-File -FilePath "start_assistant.ps1" -Encoding UTF8
Write-Host "[OK] PowerShell startup script created: start_assistant.ps1" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Get your free Groq API key: https://console.groq.com/keys" -ForegroundColor White
Write-Host "2. Run: .\setup_api_key.bat" -ForegroundColor White
Write-Host "3. Run: .\start_assistant.bat (or .\start_assistant.ps1)" -ForegroundColor White
Write-Host ""
Write-Host "Alternative models you can use:" -ForegroundColor Yellow
Write-Host "  - groq/llama-3.1-70b-versatile (recommended)" -ForegroundColor White
Write-Host "  - groq/llama-3.1-8b-instant (faster)" -ForegroundColor White
Write-Host "  - groq/mixtral-8x7b-32768 (alternative)" -ForegroundColor White
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "- If OpenInterpreter fails to install, try: pip install open-interpreter --no-deps" -ForegroundColor White
Write-Host "- If you get permission errors, run PowerShell as Administrator" -ForegroundColor White
Write-Host "- For offline use, consider Ollama instead" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"