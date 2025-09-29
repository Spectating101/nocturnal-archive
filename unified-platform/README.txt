R/SQL AI Assistant Package
==========================

This package contains everything needed to set up an AI assistant for R and SQL programming.

FILES INCLUDED:
==============

1. complete_windows_installer.bat
   - Main installer for Windows
   - Handles Python installation automatically
   - Creates desktop shortcuts
   - Includes uninstaller

2. setup_windows.bat
   - Basic Windows setup script
   - Requires Python to be pre-installed

3. setup_windows.ps1
   - PowerShell version of setup
   - For advanced users

4. setup_class_package.bat
   - Pre-configured package with API key
   - Ready to distribute to students

5. setup_semester_package.bat
   - 6-month limited package
   - Expires automatically for safety

6. r_sql_assistant.py
   - Simple Python script using Groq API
   - Backup option if OpenInterpreter fails

7. CLASS_SETUP_GUIDE.md
   - Original setup documentation
   - General instructions

8. WINDOWS_SETUP_GUIDE.md
   - Windows-specific documentation
   - Detailed troubleshooting

QUICK START:
============

For Students (Linux):
1. Run: chmod +x setup_student_assistant.sh && ./setup_student_assistant.sh
2. Start: search for "R/SQL Assistant" in your apps, or run ./run_assistant.sh

For Students (Windows):
1. Run: complete_windows_installer.bat
2. Follow prompts
3. Use desktop shortcut to start

For Professor:
1. Get Groq API key from: https://console.groq.com/keys
2. Edit setup_class_package.bat with your API key
3. Distribute to students

IMPORTANT NOTES:
================

- This package expires in 6 months for safety
- Free tier: 14,400 requests/day
- Requires internet connection
- Works with R Studio terminal

SUPPORT:
========

For questions or issues, contact your professor.

Created: September 2024
Expires: March 2025