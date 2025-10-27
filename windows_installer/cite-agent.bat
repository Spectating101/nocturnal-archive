@echo off
REM Cite-Agent launcher wrapper for Windows
REM This fixes the PATH issue with Microsoft Store Python

python -m cite_agent.cli %*
