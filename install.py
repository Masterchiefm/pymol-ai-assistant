"""
PyMOL AI Assistant Plugin - 手动安装脚本

使用方法:
1. 将 pymol-ai-assistant 文件夹复制到 PyMOL 插件目录
2. 或者在 PyMOL 命令行中运行: run install.py
"""

import sys
import os
import shutil
from pathlib import Path

def get_pymol_plugin_dir():
    """获取 PyMOL 插件目录"""
    # 尝试多种方式获取插件目录
    
    # 方式 1: 通过 PyMOL 配置
    try:
        import pymol
        from pymol import plugins
        paths = plugins.get_startup_path()
        if paths:
            return Path(paths[0])
    except:
        pass
    
    # 方式 2: 常见路径
    home = Path.home()
    common_paths = [
        home / ".pymol" / "startup",
        home / "AppData" / "Roaming" / "PyMOL" / "startup",  # Windows
        home / "Library" / "Preferences" / "PyMOL" / "startup",  # macOS
        home / ".local" / "share" / "pymol" / "startup",  # Linux
    ]
    
    for path in common_paths:
        if path.exists():
            return path
    
    # 如果都不存在，返回默认路径并创建
    if sys.platform == "win32":
        default = home / "AppData" / "Roaming" / "PyMOL" / "startup"
    elif sys.platform == "darwin":
        default = home / "Library" / "Preferences" / "PyMOL" / "startup"
    else:
        default = home / ".pymol" / "startup"
    
    default.mkdir(parents=True, exist_ok=True)
    return default

def install_plugin():
    """安装插件"""
    # 获取当前脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    plugin_name = "pymol-ai-assistant"
    
    # 获取 PyMOL 插件目录
    plugin_dir = get_pymol_plugin_dir()
    target_dir = plugin_dir / plugin_name
    
    print(f"PyMOL AI Assistant 插件安装")
    print(f"=" * 40)
    print(f"源目录: {script_dir}")
    print(f"目标目录: {target_dir}")
    print(f"")
    
    # 检查必要的文件
    init_file = script_dir / "__init__.py"
    if not init_file.exists():
        print(f"错误: 找不到 {init_file}")
        print(f"请确保从正确的目录运行此脚本")
        return False
    
    # 如果目标目录已存在，先备份
    if target_dir.exists():
        backup_dir = Path(str(target_dir) + ".backup")
        print(f"备份旧版本到: {backup_dir}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(target_dir), str(backup_dir))
    
    # 复制文件
    try:
        shutil.copytree(script_dir, target_dir, ignore=shutil.ignore_patterns(
            "*.pyc", "__pycache__", "*.backup", "install.py"
        ))
        print(f"插件已安装到: {target_dir}")
        print(f"")
        print(f"请重启 PyMOL，然后在 Plugin 菜单中找到 'AI Assistant'")
        return True
    except Exception as e:
        print(f"安装失败: {e}")
        return False

def install_dependencies():
    """安装依赖"""
    print(f"检查依赖...")
    required = ["openai>=1.0.0", "aiohttp>=3.8.0"]
    
    try:
        import openai
        import aiohttp
        print(f"所有依赖已安装")
        return True
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print(f"正在安装: {required}")
        
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install"] + required,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"依赖安装成功！")
                return True
            else:
                print(f"依赖安装失败:")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"安装依赖时出错: {e}")
            return False

if __name__ == "__main__":
    print("")
    if install_dependencies():
        install_plugin()
    else:
        print("依赖安装失败，请手动运行: pip install openai>=1.0.0 aiohttp>=3.8.0")
    print("")
    input("按 Enter 键退出...")
