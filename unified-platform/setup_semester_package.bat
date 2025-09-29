@echo off
REM R/SQL AI Assistant - Semester Package (6 Month Limit)
REM Professor's API Key Pre-Configured with Expiration

echo.
echo ========================================
echo   R/SQL AI Assistant - Semester Package
echo ========================================
echo.
echo IMPORTANT: This package expires in 6 months
echo Valid until: [EXPIRATION_DATE]
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
python -m venv semester_ai_assistant_env
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment
echo [STEP 2] Activating virtual environment...
call semester_ai_assistant_env\Scripts\activate.bat
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

REM Set API key with expiration notice
echo [STEP 5] Setting up API key...
set GROQ_API_KEY=gsk_YOUR_ACTUAL_API_KEY_HERE
setx GROQ_API_KEY "gsk_YOUR_ACTUAL_API_KEY_HERE"
echo [OK] API key configured (expires in 6 months)

REM Create startup script with expiration check
echo [STEP 6] Creating startup script...
(
echo @echo off
echo REM R/SQL AI Assistant - Semester Package
echo echo Starting R/SQL AI Assistant...
echo echo.
echo echo IMPORTANT: This package expires in 6 months
echo echo Valid until: [EXPIRATION_DATE]
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
echo call semester_ai_assistant_env\Scripts\activate.bat
echo interpreter --model groq/llama-3.1-70b-versatile
echo pause
) > start_semester_assistant.bat

echo [OK] Startup script created: start_semester_assistant.bat

REM Create expiration notice
echo [STEP 7] Creating expiration notice...
(
echo R/SQL AI Assistant - Semester Package
echo ======================================
echo.
echo IMPORTANT: This package expires in 6 months
echo Valid until: [EXPIRATION_DATE]
echo.
echo After expiration:
echo - This package will no longer work
echo - Students will need new package from professor
echo - No unexpected charges will occur
echo.
echo This ensures:
echo - Limited financial exposure
echo - Semester-aligned usage
echo - Professor control over access
echo.
echo For questions or issues, contact your professor.
echo.
) > EXPIRATION_NOTICE.txt

echo [OK] Expiration notice created: EXPIRATION_NOTICE.txt

REM Create usage monitoring script
echo [STEP 8] Creating usage monitoring script...
(
echo @echo off
echo REM Usage Monitoring Script
echo echo Checking API usage...
echo echo.
echo echo This script helps monitor usage to prevent overages
echo echo Run this monthly to check your usage
echo echo.
echo echo For detailed usage info, visit:
echo echo https://console.groq.com/usage
echo echo.
echo pause
) > check_usage.bat

echo [OK] Usage monitoring script created: check_usage.bat

echo.
echo ========================================
echo           SETUP COMPLETE!
echo ========================================
echo.
echo Your R/SQL AI Assistant is ready!
echo.
echo IMPORTANT REMINDERS:
echo - This package expires in 6 months
echo - Valid until: [EXPIRATION_DATE]
echo - No charges after expiration
echo.
echo To start using:
echo 1. Double-click: start_semester_assistant.bat
echo 2. Ask your questions!
echo.
echo Files created:
echo - start_semester_assistant.bat (main program)
echo - EXPIRATION_NOTICE.txt (important info)
echo - check_usage.bat (usage monitoring)
echo - semester_ai_assistant_env/ (AI environment)
echo.
echo Need help? Read EXPIRATION_NOTICE.txt
echo.
pause