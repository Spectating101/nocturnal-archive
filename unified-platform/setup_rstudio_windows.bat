@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Windows one-click installer for running inside RStudio Terminal
:: - Creates venv in this folder
:: - Installs dependencies
:: - Prompts and saves GROQ_API_KEY (user env)
:: - Creates start_assistant.bat
:: - Launches assistant in current RStudio Terminal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%\.venv"
set "LAUNCHER=%SCRIPT_DIR%\start_assistant.bat"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python 3.8+ is required. Please install from https://www.python.org/downloads/ and ensure "Add to PATH" is checked.
  goto :end
)

echo ==^> Creating virtual environment
python -m venv "%VENV_DIR%"
if errorlevel 1 (
  echo [ERROR] Failed to create virtual environment.
  goto :end
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  goto :end
)

python -m pip install --upgrade pip >nul

if exist "%SCRIPT_DIR%\requirements.txt" (
  echo ==^> Installing dependencies from requirements.txt
  pip install -r "%SCRIPT_DIR%\requirements.txt"
) else (
  echo ==^> Installing groq
  pip install groq
)
if errorlevel 1 (
  echo [ERROR] Failed to install Python dependencies.
  goto :end
)

echo.
if "%GROQ_API_KEY%"=="" (
  set /p GROQ_API_KEY=Enter your GROQ_API_KEY (from https://console.groq.com/keys): 
)

if not "%GROQ_API_KEY%"=="" (
  echo ==^> Saving GROQ_API_KEY to your user environment
  setx GROQ_API_KEY "%GROQ_API_KEY%" >nul
) else (
  echo [WARN] GROQ_API_KEY not provided. You can set it later with:  setx GROQ_API_KEY "your-key"
)

>"%LAUNCHER%" echo @echo off
>>"%LAUNCHER%" echo setlocal EnableExtensions
>>"%LAUNCHER%" echo call "%VENV_DIR%\Scripts\activate.bat"
>>"%LAUNCHER%" echo if errorlevel 1 ^(
>>"%LAUNCHER%" echo  echo [ERROR] Could not activate virtual environment. && exit /b 1
>>"%LAUNCHER%" echo ^)
>>"%LAUNCHER%" echo python "%SCRIPT_DIR%\r_sql_assistant.py"
>>"%LAUNCHER%" echo endlocal

echo ==^> Launching assistant
call "%LAUNCHER%"

echo.
echo ==^> Next time, just run: start_assistant.bat

:end
endlocal


