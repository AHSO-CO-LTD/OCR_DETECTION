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
        # AI/ML - PyTorch (all needed submodules)
        'torch', 'torch.nn', 'torch.nn.functional', 'torch.optim',
        'torch.utils', 'torch.utils.data', 'torch.backends', 'torch.backends.cudnn',
        'torchvision', 'torchvision.datasets', 'torchvision.transforms',
        'torchvision.models', 'torchvision.io', 'torchvision.ops',
        'torchinfo', 'tqdm',
        # YOLO (ultralytics)
        'ultralytics', 'ultralytics.models', 'ultralytics.utils',
        'ultralytics.utils.callbacks', 'ultralytics.nn', 'ultralytics.engine',
        # Scikit-learn
        'sklearn', 'sklearn.model_selection', 'sklearn.preprocessing',
        'sklearn.utils', 'sklearn.metrics', 'sklearn.ensemble',
        # Vision/Image
        'cv2', 'cvzone', 'cvzone.Utils',
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageDraw', 'PIL.ImageFont',
        # PLC / Communication
        'pymodbus', 'pymodbus.client', 'pymodbus.client.sync',
        'pymcprotocol', 'pymcprotocol.type3e',
        'serial', 'serial.tools', 'serial.tools.list_ports',
        # Database
        'peewee', 'pymysql', 'pymysql.err', 'pymysql.converters',
        # Windows API
        'win32event', 'win32api', 'winerror', 'win32con',
        'win32file', 'win32pipe', 'win32serviceutil',
        # Data & Config
        'pandas', 'pandas.core', 'pandas.io', 'pandas.io.formats',
        'numpy', 'numpy.random', 'numpy.linalg',
        'yaml', 'yaml.loader', 'packaging', 'packaging.version',
        # XML & Text
        'xml', 'xml.etree', 'xml.etree.ElementTree',
        'xml.dom', 'xml.dom.minidom', 'json',
        # System & Network
        'psutil', 'psutil.sensors', 'requests', 'requests.auth',
        'bcrypt', 'pyqtgraph', 'pyqtgraph.graphicsItems',
        'colorama', 'matplotlib',  # Common dependencies
        # App modules
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
