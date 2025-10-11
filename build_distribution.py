#!/usr/bin/env python3
"""
Build distribution packages with local LLM code stripped out.
Creates backend-only client that can't be used with personal API keys.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BUILD_DIR = Path("build_dist")
DIST_DIR = Path("dist")
SOURCE_DIR = Path("cite_agent")

# Files that contain local LLM calling code to strip
FILES_TO_PATCH = {
    "enhanced_ai_agent.py": {
        "strip_imports": [
            "from groq import Groq",
            "import groq",
        ],
        "strip_methods": [
            "_init_groq_client",
            "_call_groq_direct",
            "_call_cerebras_direct",
            "_rotate_api_key",
        ],
        "replace_patterns": [
            # Replace local API key checks with backend-only
            (
                r'os\.getenv\("GROQ_API_KEY"\)',
                'None  # Distribution version: backend-only'
            ),
            (
                r'os\.getenv\("CEREBRAS_API_KEY"\)',
                'None  # Distribution version: backend-only'
            ),
        ]
    },
}

def clean_build():
    """Clean build directory"""
    print("🧹 Cleaning build directory...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    print("✓ Build directory cleaned")

def copy_source_for_patching():
    """Copy source code to build directory for patching"""
    print("📦 Copying source code...")
    dest = BUILD_DIR / "cite_agent"
    shutil.copytree(SOURCE_DIR, dest)
    print(f"✓ Source copied to {dest}")
    return dest

def strip_local_llm_code(source_dir):
    """Remove local LLM calling code from source"""
    print("✂️  Stripping local LLM code from distribution...")

    for filename, patches in FILES_TO_PATCH.items():
        filepath = source_dir / filename
        if not filepath.exists():
            print(f"⚠️  {filename} not found, skipping")
            continue

        print(f"  Processing {filename}...")

        with open(filepath, 'r') as f:
            content = f.read()

        # Add comment at top
        header = '''"""
DISTRIBUTION VERSION - Backend-only mode
Local LLM calling code has been removed from this build.
All queries go through the centralized backend.
"""

'''

        # Simple approach: Comment out methods that call LLMs directly
        # This preserves imports and structure but disables functionality

        for method in patches.get("strip_methods", []):
            # Find method definition and replace body with raise
            content = content.replace(
                f"def {method}(",
                f"def {method}(  # STRIPPED IN DISTRIBUTION\n        raise NotImplementedError('Backend-only distribution - use centralized API')  # noqa\n        #"
            )

        # Remove environment variable checks for API keys
        content = content.replace(
            'os.getenv("GROQ_API_KEY")',
            'None  # Distribution: backend-only'
        )
        content = content.replace(
            'os.getenv("CEREBRAS_API_KEY")',
            'None  # Distribution: backend-only'
        )

        # Write patched file
        with open(filepath, 'w') as f:
            f.write(header + content)

        print(f"  ✓ Patched {filename}")

    print("✓ Local LLM code stripped")

def build_distribution_package(source_dir):
    """Build PyPI package from patched source"""
    print("📦 Building distribution package...")

    # Copy setup.py to build dir
    shutil.copy("setup.py", BUILD_DIR / "setup.py")
    shutil.copy("README.md", BUILD_DIR / "README.md")
    shutil.copy("LICENSE", BUILD_DIR / "LICENSE")
    shutil.copy("requirements.txt", BUILD_DIR / "requirements.txt")
    if Path("MANIFEST.in").exists():
        shutil.copy("MANIFEST.in", BUILD_DIR / "MANIFEST.in")

    # Build from build directory
    original_dir = os.getcwd()
    os.chdir(BUILD_DIR)

    try:
        result = subprocess.run(
            [sys.executable, "setup.py", "sdist", "bdist_wheel"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False

        print("✓ Distribution package built")

        # Move dist files to main dist directory
        build_dist = Path("dist")
        if build_dist.exists():
            DIST_DIR.mkdir(exist_ok=True)
            for file in build_dist.glob("*"):
                dest = DIST_DIR / f"{file.stem}.distribution{file.suffix}"
                shutil.copy(file, dest)
                print(f"  → {dest.name}")

        return True

    finally:
        os.chdir(original_dir)

def build_pyinstaller_binary(source_dir):
    """Build standalone binary from patched source"""
    print("🔨 Building PyInstaller binary...")

    # Create temporary spec file pointing to patched source
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['{BUILD_DIR}/cite_agent/cli.py'],
    pathex=['{BUILD_DIR}'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'cite_agent.account_client',
        'cite_agent.setup_config',
        'cite_agent.enhanced_ai_agent',
        'keyring',
        'keyring.backends',
        'requests',
        'aiohttp',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'cite_agent_api',
        'tests',
        'docs',
        'pytest',
        'matplotlib',
        'pandas',
        'numpy',
        'groq',  # Remove groq since we stripped local calling
        'cerebras',  # Remove cerebras since we stripped local calling
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
    name='cite-agent-distribution',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
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

    spec_file = BUILD_DIR / "cite-agent-dist.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)

    # Run PyInstaller
    result = subprocess.run(
        ["pyinstaller", "--clean", str(spec_file)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ PyInstaller failed: {result.stderr}")
        return False

    print("✓ Binary built")

    # Copy binary to dist
    binary_path = BUILD_DIR / "dist" / "cite-agent-distribution"
    if binary_path.exists():
        dest = DIST_DIR / "cite-agent.distribution"
        shutil.copy(binary_path, dest)
        os.chmod(dest, 0o755)
        print(f"  → {dest.name}")

    return True

def main():
    print("=" * 60)
    print("🚀 Building Distribution (Backend-Only)")
    print("=" * 60)
    print()

    # Clean and prepare
    clean_build()

    # Copy source
    patched_source = copy_source_for_patching()

    # Strip local LLM code
    strip_local_llm_code(patched_source)

    # Build PyPI package
    if not build_distribution_package(patched_source):
        print("❌ Distribution build failed")
        return 1

    # Build binary
    # if not build_pyinstaller_binary(patched_source):
    #     print("❌ Binary build failed")
    #     return 1

    print()
    print("=" * 60)
    print("✅ Distribution Build Complete!")
    print("=" * 60)
    print()
    print("📦 Distribution files (backend-only):")
    for file in DIST_DIR.glob("*.distribution*"):
        print(f"  - {file.name} ({file.stat().st_size // 1024}KB)")
    print()
    print("🔒 Security: Local LLM code stripped")
    print("   Users MUST use backend - cannot supply own API keys")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
