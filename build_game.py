"""
Arcade 游戏打包脚本 - 使用 PyInstaller
"""
import os
import sys
from pathlib import Path


def create_spec_file():
    """创建 PyInstaller spec 文件"""
    
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    
    # 收集所有需要包含的数据文件
    data_files = []
    
    # 添加资源文件
    assets_dir = project_root / "assets"
    if assets_dir.exists():
        data_files.append((str(assets_dir), "assets"))
    
    # 添加卡牌数据文件
    cards_dir = project_root / "cards"
    if cards_dir.exists():
        data_files.append((str(cards_dir), "cards"))
    
    # 添加 JSON 配置文件
    json_files = [
        "cards.json",
        "equipments.json",
    ]
    for json_file in json_files:
        file_path = project_root / json_file
        if file_path.exists():
            data_files.append((str(file_path), "."))
    
    # 添加 careers 模块
    careers_dir = project_root / "careers"
    if careers_dir.exists():
        data_files.append((str(careers_dir), "careers"))
    
    # 生成 spec 文件内容
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 数据文件列表
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas={data_files},
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
    hooksconfig={{}},
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
    console=True,  # 设置为 False 可以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定
)
'''
    
    spec_file = project_root / "game.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ Spec 文件已创建: {spec_file}")
    return spec_file


def build_game():
    """打包游戏"""
    import subprocess
    
    project_root = Path(__file__).parent.absolute()
    
    # 首先创建 spec 文件
    spec_file = create_spec_file()
    
    print("\n开始打包游戏...")
    print("=" * 60)
    
    # 使用 PyInstaller 打包
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        str(spec_file)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            check=True,
            capture_output=False
        )
        
        print("\n" + "=" * 60)
        print("✓ 打包完成！")
        print("=" * 60)
        
        # 输出文件位置
        dist_dir = project_root / "dist"
        exe_path = dist_dir / "CardBattleGame.exe"
        
        if exe_path.exists():
            print(f"\n可执行文件位置: {exe_path}")
            print(f"文件大小: {exe_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            print("\n警告: 未找到生成的可执行文件")
        
        print("\n注意事项:")
        print("1. 首次运行可能需要安装 Visual C++ Redistributable")
        print("2. 如果需要自定义图标，请准备 .ico 文件并在 spec 文件中配置")
        print("3. 打包后的程序在 dist/CardBattleGame.exe")
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ 错误: 未找到 PyInstaller")
        print("请先安装: pip install pyinstaller")
        return False
    
    return True


if __name__ == "__main__":
    print("Arcade 卡牌游戏打包工具")
    print("=" * 60)
    
    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("✗ 未检测到 PyInstaller")
        print("\n正在安装 PyInstaller...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller 安装完成")
    
    # 开始打包
    build_game()
