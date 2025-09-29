#!/usr/bin/env python3
"""
Install missing dependencies
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

print("🚀 Installing missing dependencies...")

# Install required packages
packages = [
    "httpx",
    "structlog",
    "pydantic",
    "requests"
]

success_count = 0
for package in packages:
    if install_package(package):
        success_count += 1

print(f"\n🎉 Installed {success_count}/{len(packages)} packages successfully")