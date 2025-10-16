#!/usr/bin/env python3
"""
Build script for protected client distribution
Obfuscates code and creates installers
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
OBFUSCATED_DIR = BUILD_DIR / "obfuscated"
CLIENT_DIR = Path("cite_agent")

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning build directories...")
    for dir_path in [BUILD_DIR, DIST_DIR, OBFUSCATED_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)

    # Remove pycache
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))
        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo"):
                os.remove(os.path.join(root, file))

    print("✓ Build directories cleaned")

def obfuscate_code():
    """Obfuscate Python source code with PyArmor"""
    print("🔒 Obfuscating client code with PyArmor...")

    OBFUSCATED_DIR.mkdir(parents=True, exist_ok=True)

    # Obfuscate cite_agent package
    cmd = [
        "pyarmor",
        "gen",
        "--output", str(OBFUSCATED_DIR / "cite_agent"),
        "--recursive",
        "--enable-jit",  # JIT compilation for better performance and protection
        "--private",     # Extra protection layer
        str(CLIENT_DIR)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Obfuscation failed: {result.stderr}")
        return False

    print("✓ Code obfuscated successfully")
    return True

def create_pyinstaller_spec():
    """Create PyInstaller spec file for bundling"""
    print("📦 Creating PyInstaller spec...")

    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cite_agent/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('cite_agent/*.py', 'cite_agent'),
        ('cite_agent/account_client.py', 'cite_agent'),
        ('cite_agent/setup_config.py', 'cite_agent'),
    ],
    hiddenimports=[
        'cite_agent.account_client',
        'cite_agent.setup_config',
        'cite_agent.enhanced_ai_agent',
        'keyring',
        'keyring.backends',
        'requests',
        'aiohttp',
        'groq',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'cite_agent_api',  # Exclude server code
        'tests',
        'docs',
        'pytest',
        'matplotlib',
        'pandas',
        'numpy',  # Heavy deps not needed for client
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='cite-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols
    upx=True,    # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    with open("cite-agent.spec", "w") as f:
        f.write(spec_content)

    print("✓ PyInstaller spec created")

def build_binary():
    """Build binary executable with PyInstaller"""
    print("🔨 Building binary executable...")

    cmd = ["pyinstaller", "--clean", "cite-agent.spec"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Binary build failed: {result.stderr}")
        return False

    print("✓ Binary built successfully")
    return True

def create_setup_py():
    """Create setup.py for PyPI distribution"""
    print("📄 Creating setup.py for PyPI...")

    # Rename setup.py.disabled to setup.py
    if Path("setup.py.disabled").exists():
        shutil.copy("setup.py.disabled", "setup.py")

    # Update to use obfuscated code if available
    setup_content = """#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="cite-agent",
    version="1.0.0",
    author="Cite-Agent Team",
    author_email="contact@citeagent.dev",
    description="Terminal AI assistant for academic research with citation verification",
    long_description=open("README.md").read() if Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    url="https://github.com/Spectating101/cite-agent",
    packages=find_packages(exclude=["tests", "docs", "cite-agent-api", "cite_agent_api"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.9.0",
        "groq>=0.4.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "rich>=13.7.0",
        "keyring>=24.3.0",
    ],
    entry_points={
        "console_scripts": [
            "cite-agent=cite_agent.cli:main",
            "nocturnal=cite_agent.cli:main",
        ],
    },
)
"""

    with open("setup.py", "w") as f:
        f.write(setup_content)

    print("✓ setup.py created")

def build_pypi_package():
    """Build package for PyPI distribution"""
    print("📦 Building PyPI package...")

    cmd = ["python", "setup.py", "sdist", "bdist_wheel"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Package build failed: {result.stderr}")
        return False

    print("✓ PyPI package built")
    print(f"  - Source: dist/*.tar.gz")
    print(f"  - Wheel: dist/*.whl")
    return True

def main():
    """Main build process"""
    print("=" * 60)
    print("🚀 Cite-Agent Protected Build System")
    print("=" * 60)
    print()

    # Clean previous builds
    clean_build()

    # Obfuscate code
    if not obfuscate_code():
        print("⚠️  Continuing without obfuscation (PyArmor failed)")

    # Create PyPI package
    create_setup_py()
    if not build_pypi_package():
        print("❌ PyPI package build failed")
        return 1

    # Create PyInstaller spec and build binary
    create_pyinstaller_spec()
    if not build_binary():
        print("❌ Binary build failed")
        return 1

    print()
    print("=" * 60)
    print("✅ Build complete!")
    print("=" * 60)
    print()
    print("📦 Distribution artifacts:")
    print(f"  - PyPI package: dist/*.whl")
    print(f"  - Binary: dist/cite-agent")
    print()
    print("Next steps:")
    print("  1. Test: pip install dist/*.whl")
    print("  2. Publish to PyPI: twine upload dist/*")
    print("  3. Create installers from binary")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
