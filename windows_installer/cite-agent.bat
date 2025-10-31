@echo off
REM Cite-Agent launcher wrapper for Windows
REM Tries Python launcher first, then python.exe fallback.

where py >nul 2>&1
if %errorlevel%==0 (
    py -m cite_agent.cli %*
    exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel%==0 (
    python -m cite_agent.cli %*
    exit /b %errorlevel%
)

echo.
echo [Cite-Agent] Unable to locate Python on PATH.
echo Please reopen your terminal or log out/in so PATH updates apply.
echo If the problem persists, reinstall using the Cite-Agent installer.
exit /b 1
