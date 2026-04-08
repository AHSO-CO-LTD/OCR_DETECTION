# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for OCR Detection System v1.2.0 (Windows)
"""

a = Analysis(
    ['main.py'],
    pathex=['lib'],
    binaries=[],
    datas=[
        ('form_UI', 'form_UI'),
    ],
    hiddenimports=[
        # PyQt5
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'PyQt5.uic', 'PyQt5.QtMultimedia', 'PyQt5.sip',
        # AI/ML - PyTorch
        'torch', 'torch.nn', 'torch.nn.functional', 'torch.optim',
        'torch.utils', 'torch.utils.data',
        # Torchvision (for models and transforms)
        'torchvision', 'torchvision.datasets', 'torchvision.transforms',
        'torchvision.models',
        # Torch info and progress
        'torchinfo', 'tqdm',
        # YOLO (ultralytics)
        'ultralytics', 'ultralytics.models', 'ultralytics.utils',
        # Scikit-learn
        'sklearn', 'sklearn.model_selection', 'sklearn.preprocessing',
        'sklearn.utils', 'sklearn.metrics',
        # Vision
        'cv2', 'cvzone', 'cvzone.Utils',
        'PIL', 'PIL.Image', 'PIL.ImageTk',
        # PLC / Communication
        'pymodbus', 'pymodbus.client',
        'pymcprotocol',
        'serial', 'serial.tools', 'serial.tools.list_ports',
        # Database
        'peewee', 'pymysql', 'pymysql.err',
        # Windows API
        'win32event', 'win32api', 'winerror', 'win32con',
        # Data & Config
        'pandas', 'numpy', 'yaml', 'packaging', 'packaging.version',
        # XML
        'xml', 'xml.etree', 'xml.etree.ElementTree', 'xml.dom', 'xml.dom.minidom',
        # System & Network
        'psutil', 'requests', 'bcrypt', 'pyqtgraph',
        # App modules (core functionality)
        'lib', 'lib.StackUI', 'lib.Global', 'lib.Database', 'lib.Camera_Program',
        'lib.PLC', 'lib.Login_Screen', 'lib.Main_Screen',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DRB-OCR-AI',
    debug=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DRB-OCR-AI'
)
