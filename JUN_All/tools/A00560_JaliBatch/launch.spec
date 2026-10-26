# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('../../Framework/styles', 'Framework/styles'),
         # mayapy 워커는 디스크의 .py 를 읽어야 한다 - 워커와 그것이 import 하는 Framework 모듈을 그대로 싣는다
         ('app/maya', 'tools/A00560_JaliBatch/app/maya'),
         ('../../Framework/jali', 'Framework/jali'),
         ('../../Framework/core', 'Framework/core'),
         ('icon', 'icon')]
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
    name='A00560_JaliBatch',
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
    icon='icon/A00560_JaliBatch.ico',
)
