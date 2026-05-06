# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 数据文件列表
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\PythonProject\\PythonProject\\assets', 'assets'), ('D:\\PythonProject\\PythonProject\\cards', 'cards'), ('D:\\PythonProject\\PythonProject\\cards.json', '.'), ('D:\\PythonProject\\PythonProject\\equipments.json', '.'), ('D:\\PythonProject\\PythonProject\\careers', 'careers')],
    hiddenimports=[
        'arcade',
        'pyglet',
        'numpy',
        'matplotlib',
        'careers.artisan_passive',
        'careers.drifter_passive',
        'careers.farmer_passive',
        'careers.pedlar_passive',
        'careers.scholar_passive',
    ],
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
    name='CardBattleGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为 False 可以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定
)
