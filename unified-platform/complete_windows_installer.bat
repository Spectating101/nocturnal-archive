@echo off
REM Complete Windows Installer for R/SQL AI Assistant
REM Handles Python installation and all dependencies

echo.
echo ========================================
echo   Complete R/SQL AI Assistant Installer
echo ========================================
echo.
echo This installer will:
echo 1. Check/Install Python if needed
echo 2. Set up AI assistant environment
echo 3. Configure everything automatically
echo.
echo IMPORTANT: This package expires in 6 months
echo Valid until: [EXPIRATION_DATE]
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python is not installed or not in PATH
    echo.
    echo Would you like to download and install Python automatically?
    echo This will open the Python download page.
    echo.
    set /p choice="Download Python? (y/n): "
    if /i "%choice%"=="y" (
        echo [INFO] Opening Python download page...
        start https://www.python.org/downloads/
        echo.
        echo Please:
        echo 1. Download Python 3.8 or newer
        echo 2. Run the installer
        echo 3. CHECK "Add Python to PATH" during installation
        echo 4. Restart this script after installation
        echo.
        pause
        exit /b 1
    ) else (
        echo [ERROR] Python is required to continue
        echo Please install Python manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo [OK] Python found: 
python --version

REM Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.8 or newer is required
    echo Current version is too old. Please upgrade Python.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python version is compatible

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not available
    echo Please reinstall Python with pip included
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] pip found
echo.

REM Create virtual environment
echo [STEP 1] Creating virtual environment...
python -m venv r_sql_ai_env
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    echo This might be due to:
    echo - Insufficient disk space
    echo - Permission issues
    echo - Corrupted Python installation
    echo.
    echo Try running as Administrator or check disk space.
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment
echo [STEP 2] Activating virtual environment...
call r_sql_ai_env\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    echo This might be due to:
    echo - Antivirus blocking the script
    echo - Permission issues
    echo - Corrupted virtual environment
    echo.
    echo Try running as Administrator or disable antivirus temporarily.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip
echo [STEP 3] Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [WARNING] Failed to upgrade pip, continuing with current version...
) else (
    echo [OK] pip upgraded
)

REM Install OpenInterpreter
echo [STEP 4] Installing OpenInterpreter...
echo This may take several minutes...
echo.
pip install open-interpreter
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install OpenInterpreter
    echo.
    echo Trying alternative installation method...
    pip install open-interpreter --no-deps
    if %errorlevel% neq 0 (
        echo [ERROR] Alternative installation also failed
        echo.
        echo This might be due to:
        echo - Internet connection issues
        echo - Antivirus blocking downloads
        echo - Corporate firewall restrictions
        echo.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    ) else (
        echo [OK] OpenInterpreter installed (minimal dependencies)
        echo [WARNING] Some features may not work due to missing dependencies
    )
) else (
    echo [OK] OpenInterpreter installed successfully
)

REM Set API key
echo [STEP 5] Setting up API key...
set GROQ_API_KEY=gsk_YOUR_ACTUAL_API_KEY_HERE
setx GROQ_API_KEY "gsk_YOUR_ACTUAL_API_KEY_HERE"
if %errorlevel% neq 0 (
    echo [WARNING] Failed to set permanent API key
    echo API key is set for current session only
) else (
    echo [OK] API key configured permanently
)

REM Create startup script
echo [STEP 6] Creating startup script...
(
echo @echo off
echo REM R/SQL AI Assistant - Ready to Use!
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
echo call r_sql_ai_env\Scripts\activate.bat
echo interpreter --model groq/llama-3.1-70b-versatile
echo pause
) > start_ai_assistant.bat

echo [OK] Startup script created: start_ai_assistant.bat

REM Create desktop shortcut
echo [STEP 7] Creating desktop shortcut...
(
echo Set oWS = WScript.CreateObject("WScript.Shell")
echo sLinkFile = "%USERPROFILE%\Desktop\R-SQL AI Assistant.lnk"
echo Set oLink = oWS.CreateShortcut(sLinkFile)
echo oLink.TargetPath = "%~dp0start_ai_assistant.bat"
echo oLink.WorkingDirectory = "%~dp0"
echo oLink.Description = "R/SQL AI Assistant"
echo oLink.Save
) > create_shortcut.vbs
cscript create_shortcut.vbs >nul 2>&1
del create_shortcut.vbs
echo [OK] Desktop shortcut created

REM Create uninstaller
echo [STEP 8] Creating uninstaller...
(
echo @echo off
echo REM Uninstaller for R/SQL AI Assistant
echo echo Uninstalling R/SQL AI Assistant...
echo echo.
echo echo This will remove:
echo echo - Virtual environment
echo echo - Startup scripts
echo echo - Desktop shortcut
echo echo.
echo set /p choice="Are you sure? (y/n): "
echo if /i "%%choice%%"=="y" (
echo     echo Removing files...
echo     rmdir /s /q r_sql_ai_env
echo     del start_ai_assistant.bat
echo     del "%%USERPROFILE%%\Desktop\R-SQL AI Assistant.lnk"
echo     echo.
echo     echo Uninstallation complete!
echo ) else (
echo     echo Uninstallation cancelled.
echo )
echo pause
) > uninstall.bat

echo [OK] Uninstaller created: uninstall.bat

REM Create system info file
echo [STEP 9] Creating system info...
(
echo R/SQL AI Assistant - System Information
echo ======================================
echo.
echo Installation Date: %DATE% %TIME%
echo Python Version: 
python --version
echo.
echo System Information:
echo - OS: %OS%
echo - Architecture: %PROCESSOR_ARCHITECTURE%
echo - User: %USERNAME%
echo - Computer: %COMPUTERNAME%
echo.
echo Package Information:
echo - Expires: [EXPIRATION_DATE]
echo - Model: groq/llama-3.1-70b-versatile
echo - Environment: r_sql_ai_env
echo.
echo Files Created:
echo - start_ai_assistant.bat (main program)
echo - uninstall.bat (removal tool)
echo - r_sql_ai_env/ (AI environment)
echo - Desktop shortcut
echo.
) > system_info.txt

echo [OK] System info created: system_info.txt

echo.
echo ========================================
echo           INSTALLATION COMPLETE!
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
echo 1. Double-click: start_ai_assistant.bat
echo 2. Or use desktop shortcut: "R-SQL AI Assistant"
echo 3. Ask your questions!
echo.
echo Files created:
echo - start_ai_assistant.bat (main program)
echo - uninstall.bat (removal tool)
echo - system_info.txt (installation details)
echo - Desktop shortcut
echo - r_sql_ai_env/ (AI environment)
echo.
echo Need help? Read system_info.txt
echo.
pause