# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('../../Framework/styles', 'Framework/styles'),
         # Maya 탭의 mayapy 워커와 그 코어 - mayapy 가 디스크의 .py 를 읽어야 하므로 그대로 싣는다 (v01.35)
         ('app/maya/core', 'tools/A00210_FileManager/app/maya/core'),
         # v01.41 Export 하위탭의 워커가 Framework.core.maya_fbx · Framework.jali.time_units 를 import 한다 (A00560 과 같은 규칙)
         ('../../Framework/core', 'Framework/core'),
         ('../../Framework/jali', 'Framework/jali')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['launch.py'],
    pathex=['../../', '.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='A00210_FileManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
