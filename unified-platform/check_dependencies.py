#!/usr/bin/env python3
"""
Check Dependencies
"""

import sys

def check_package(package_name):
    """Check if a package is installed"""
    try:
        __import__(package_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed")
        return False

print("🔍 Checking Dependencies")
print("=" * 30)

packages = [
    "groq",
    "fastapi", 
    "uvicorn",
    "pydantic",
    "requests",
    "structlog",
    "httpx",
    "asyncio"
]

installed = 0
for package in packages:
    if check_package(package):
        installed += 1

print(f"\n📊 Summary: {installed}/{len(packages)} packages installed")

if installed < len(packages):
    print("\n💡 To install missing packages:")
    print("pip install httpx structlog")
else:
    print("\n🎉 All dependencies are installed!")