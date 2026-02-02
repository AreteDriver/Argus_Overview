# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Argus Overview (Windows)

Build with: pyinstaller Argus_Overview.spec

Output: dist/Argus_Overview.exe (single file executable)
"""

import sys
from pathlib import Path

block_cipher = None

# Paths
src_path = Path('src')
icon_path = Path('assets/icon.ico')

# Data files to include
datas = [
    # Sound files for intel alerts
    (str(src_path / 'argus_overview' / 'intel' / 'sounds' / '*.wav'), 'argus_overview/intel/sounds'),
    # README and docs
    ('README.md', '.'),
    ('CHANGELOG.md', '.'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtMultimedia',
    'argus_overview.platform.windows',
    'argus_overview.platform.base',
    'win32api',
    'win32con',
    'win32gui',
    'win32ui',
    'win32process',
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
]

# Exclude these modules (not needed, reduce size)
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'pandas',
    '_tkinter',
    'IPython',
    'jupyter',
]

a = Analysis(
    ['src/main.py'],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='Argus_Overview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)
