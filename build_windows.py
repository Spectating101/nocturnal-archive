#!/usr/bin/env python3
"""
Build standalone Windows executable with PyInstaller
No Python installation required for end users
"""

import subprocess
import sys
from pathlib import Path

def build_windows_exe():
    """Build cite-agent.exe for Windows"""
    
    print("Building Windows executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Single .exe file
        "--name=cite-agent",
        "--add-data=cite_agent/data:cite_agent/data",  # Include data files
        "--hidden-import=cite_agent.cli",
        "--hidden-import=cite_agent.enhanced_ai_agent",
        "--hidden-import=aiohttp",
        "--hidden-import=groq",
        "--hidden-import=rich",
        "--icon=NONE",  # Add icon later
        "--console",  # Keep console window
        "cite_agent/cli.py"
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n✅ Windows executable created: dist/cite-agent.exe")
    print("\nUsers can:")
    print("1. Download cite-agent.exe")
    print("2. Double-click to run")
    print("3. Or run from cmd: cite-agent.exe \"Find papers on AI\"")
    print("\nNo Python installation required!")

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    build_windows_exe()

