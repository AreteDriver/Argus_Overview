# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Argus Overview v2.4 Windows build
Creates standalone .exe with all dependencies bundled
"""
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect all PySide6 data files and binaries
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')

a = Analysis(
    ['src/main.py'],
    pathex=[os.path.abspath('src')],
    binaries=pyside6_binaries,
    datas=[
        ('../assets', 'assets'),
    ] + pyside6_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'win32gui',
        'win32ui',
        'win32con',
        'win32api',
        'PIL',
        'PIL.Image',
        'PIL.ImageQt',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        'pynput.mouse',
        'pynput.mouse._win32',
        'watchdog',
        'watchdog.observers',
        'watchdog.observers.read_directory_changes',
        'watchdog.events',
    ] + pyside6_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'tkinter',
        'PyQt5',
        'PyQt6',
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
    name='Argus-Overview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/icon.ico' if os.path.exists('../assets/icon.ico') else None,
    version_file=None,
)
