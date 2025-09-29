#!/usr/bin/env python3
"""
Install requests dependency
"""

import subprocess
import sys

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("✅ requests installed successfully")
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to install requests: {e}")