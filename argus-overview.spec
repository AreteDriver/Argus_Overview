# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Argus Overview (Linux)

Build with: pyinstaller argus-overview.spec

Output: dist/argus-overview (executable for AppImage packaging)
"""

from pathlib import Path

block_cipher = None

# Paths
src_path = Path('src')
icon_path = Path('assets/icon.png')

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
    'argus_overview.platform.linux',
    'argus_overview.platform.base',
    'pynput.keyboard._xorg',
    'pynput.mouse._xorg',
    'Xlib',
    'Xlib.display',
    'Xlib.X',
    'Xlib.Xatom',
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
    name='argus-overview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX disabled on Linux due to compatibility issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
