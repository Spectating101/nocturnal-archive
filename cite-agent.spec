# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for cite-agent
Creates standalone executable with all dependencies bundled
Excludes unnecessary files and server code
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all cite_agent modules
cite_agent_hiddenimports = collect_submodules('cite_agent')

# Additional hidden imports
hiddenimports = cite_agent_hiddenimports + [
    'keyring',
    'keyring.backends',
    'keyring.backends.SecretService',
    'keyring.backends.Windows',
    'keyring.backends.macOS',
    'requests',
    'aiohttp',
    'groq',
    'pydantic',
    'rich',
    'dotenv',
]

# Data files
datas = []

# Binaries (none needed for pure Python)
binaries = []

a = Analysis(
    ['cite_agent/cli.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude server code
        'cite_agent_api',
        'cite-agent-api',

        # Exclude tests and docs
        'tests',
        'docs',
        'pytest',
        'unittest',

        # Exclude heavy scientific libs not needed
        'matplotlib',
        'pandas',
        'numpy',
        'scipy',
        'sklearn',

        # Exclude dev tools
        'pip',
        'setuptools',
        'wheel',
        'pyinstaller',

        # Exclude unused stdlib
        'tkinter',
        'turtle',
        'test',
        'pydoc',
        'doctest',
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
    strip=True,  # Strip debug symbols (smaller binary)
    upx=True,    # Compress with UPX (much smaller)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI application needs console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon file
)
