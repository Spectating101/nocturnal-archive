@echo off
REM Pre-Packaged R/SQL AI Assistant for Class
REM Professor's API Key Pre-Configured

echo.
echo ========================================
echo   R/SQL AI Assistant - Class Package
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

REM Create virtual environment
echo [STEP 1] Creating virtual environment...
python -m venv class_ai_assistant_env
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment
echo [STEP 2] Activating virtual environment...
call class_ai_assistant_env\Scripts\activate.bat
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

REM Set API key (replace with your actual key)
echo [STEP 5] Setting up API key...
set GROQ_API_KEY=gsk_YOUR_ACTUAL_API_KEY_HERE
setx GROQ_API_KEY "gsk_YOUR_ACTUAL_API_KEY_HERE"
echo [OK] API key configured

REM Create startup script
echo [STEP 6] Creating startup script...
(
echo @echo off
echo REM R/SQL AI Assistant - Ready to Use!
echo echo Starting R/SQL AI Assistant...
echo echo.
echo echo This assistant can help you with:
echo echo - R programming commands
echo echo - SQL queries and syntax
echo echo - Data analysis tasks
echo echo - Code debugging and improvement
echo echo.
echo echo Type your questions and press Enter!
echo echo Type 'quit' to exit.
echo echo.
echo call class_ai_assistant_env\Scripts\activate.bat
echo interpreter --model groq/llama-3.1-70b-versatile
echo pause
) > start_ai_assistant.bat

echo [OK] Startup script created: start_ai_assistant.bat

REM Create quick start guide
echo [STEP 7] Creating quick start guide...
(
echo R/SQL AI Assistant - Quick Start Guide
echo ======================================
echo.
echo 1. Double-click: start_ai_assistant.bat
echo 2. Wait for AI to load (may take 30 seconds)
echo 3. Ask your questions!
echo.
echo Example Questions:
echo - "How do I create a histogram in R?"
echo - "What's the SQL syntax for JOIN?"
echo - "Help me debug this R code"
echo - "How do I filter data in R?"
echo.
echo Tips:
echo - Be specific in your questions
echo - Ask follow-up questions
echo - Type 'quit' to exit
echo.
echo Troubleshooting:
echo - If it doesn't start, run as Administrator
echo - If Python errors, reinstall Python with PATH
echo - If API errors, contact professor
echo.
) > QUICK_START_GUIDE.txt

echo [OK] Quick start guide created: QUICK_START_GUIDE.txt

echo.
echo ========================================
echo           SETUP COMPLETE!
echo ========================================
echo.
echo Your R/SQL AI Assistant is ready!
echo.
echo To start using:
echo 1. Double-click: start_ai_assistant.bat
echo 2. Ask your questions!
echo.
echo Files created:
echo - start_ai_assistant.bat (main program)
echo - QUICK_START_GUIDE.txt (instructions)
echo - class_ai_assistant_env/ (AI environment)
echo.
echo Need help? Read QUICK_START_GUIDE.txt
echo.
pause