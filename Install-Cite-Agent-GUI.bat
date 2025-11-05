@echo off
REM Cite-Agent GUI Installer Launcher
REM Double-click this file to launch the graphical installer

REM Get the directory where this .bat file is located
set "SCRIPT_DIR=%~dp0"

REM Launch the PowerShell GUI installer
powershell -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%Install-Cite-Agent-GUI.ps1"

REM If that fails, try with full path resolution
if %errorlevel% neq 0 (
    powershell -ExecutionPolicy Bypass -NoProfile -Command "& '%SCRIPT_DIR%Install-Cite-Agent-GUI.ps1'"
)
