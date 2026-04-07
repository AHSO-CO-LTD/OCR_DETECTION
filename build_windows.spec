# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OCR Detection System v1.1.0 (Windows)
Builds Windows .exe with all dependencies
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('form_UI', 'form_UI'),
        ('assets', 'assets'),
        ('config.yaml.example', '.'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.uic',
        'lib.Global',
        'lib.Database',
        'lib.Authentication',
        'lib.Camera_Program',
        'lib.PLC',
        'lib.QTimerPollHandler',
        'lib.QTimerPLCController',
        'lib.Display',
        'lib.UpdateChecker',
        'lib.version',
        'peewee',
        'pymysql',
        'cv2',
        'numpy',
        'torch',
        'ultralytics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='DRB-OCR-AI',
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
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DRB-OCR-AI'
)
