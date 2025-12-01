# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# __file__ 在 spec 执行时可能不存在，使用当前工作目录兜底
project_root = os.path.abspath(os.getcwd())

# 需要打包的静态资源
_datas = [
    (os.path.join(project_root, "names-dataset.txt"), "."),
]
_turnstile_dir = os.path.join(project_root, "turnstilePatch")
if os.path.isdir(_turnstile_dir):
    _datas.append((_turnstile_dir, "turnstilePatch"))

_hiddenimports = collect_submodules("DrissionPage")

a = Analysis(
    ["gemini_auto_register.py"],
    pathex=[project_root],
    binaries=[],
    datas=_datas,
    hiddenimports=_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="GeminiAutoRegister",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GeminiAutoRegister",
)
