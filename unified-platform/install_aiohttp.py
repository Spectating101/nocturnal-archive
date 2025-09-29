#!/usr/bin/env python3
"""
Install aiohttp dependency
"""

import subprocess
import sys

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    print("✅ aiohttp installed successfully")
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to install aiohttp: {e}")