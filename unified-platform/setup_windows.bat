@echo off
REM Windows Setup Script for OpenInterpreter + Groq
REM R/SQL AI Assistant Setup for Students

echo.
echo ========================================
echo   R/SQL AI Assistant Setup for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python found: 
python --version

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo [OK] pip found
echo.

REM Create virtual environment
echo [STEP 1] Creating virtual environment...
python -m venv r_sql_assistant_env
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment
echo [STEP 2] Activating virtual environment...
call r_sql_assistant_env\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip
echo [STEP 3] Upgrading pip...
python -m pip install --upgrade pip
echo [OK] pip upgraded

REM Install OpenInterpreter
echo [STEP 4] Installing OpenInterpreter...
echo This may take several minutes...
pip install open-interpreter
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install OpenInterpreter
    echo.
    echo Alternative: Try installing with --no-deps flag:
    echo pip install open-interpreter --no-deps
    echo.
    pause
    exit /b 1
)
echo [OK] OpenInterpreter installed

REM Create startup script
echo [STEP 5] Creating startup script...
(
echo @echo off
echo REM R/SQL AI Assistant Startup Script
echo echo Starting R/SQL AI Assistant with Groq...
echo echo.
echo echo Make sure you have set your GROQ_API_KEY:
echo echo set GROQ_API_KEY=your-key-here
echo echo.
echo call r_sql_assistant_env\Scripts\activate.bat
echo interpreter --model groq/llama-3.1-70b-versatile
echo pause
) > start_assistant.bat

echo [OK] Startup script created: start_assistant.bat

REM Create API key setup script
echo [STEP 6] Creating API key setup script...
(
echo @echo off
echo REM Set your Groq API Key
echo echo Setting up Groq API Key...
echo echo.
echo set /p api_key="Enter your Groq API Key: "
echo setx GROQ_API_KEY "%api_key%"
echo echo.
echo echo API Key set successfully!
echo echo You may need to restart your terminal for changes to take effect.
echo echo.
echo pause
) > setup_api_key.bat

echo [OK] API key setup script created: setup_api_key.bat

echo.
echo ========================================
echo           SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Get your free Groq API key: https://console.groq.com/keys
echo 2. Run: setup_api_key.bat
echo 3. Run: start_assistant.bat
echo.
echo Alternative models you can use:
echo   - groq/llama-3.1-70b-versatile ^(recommended^)
echo   - groq/llama-3.1-8b-instant ^(faster^)
echo   - groq/mixtral-8x7b-32768 ^(alternative^)
echo.
echo Troubleshooting:
echo - If OpenInterpreter fails to install, try: pip install open-interpreter --no-deps
echo - If you get permission errors, run as Administrator
echo - For offline use, consider Ollama instead
echo.
pause