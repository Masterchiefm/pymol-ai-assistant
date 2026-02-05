"""
PyMOL AI Assistant Plugin

使用 AI 工具技能控制 PyMOL 分子可视化软件。
功能：
- 流式显示 AI 思考与输出
- 记录和切换 API 配置
- 记录和显示操作日志
- AI 工具控制 PyMOL

Author: AI Assistant
Version: 1.2.0
"""

__version__ = "1.2.0"

import sys
import os
import subprocess
import importlib
from pathlib import Path

# 插件根目录
PLUGIN_DIR = Path(__file__).parent.absolute()

def ensure_dependencies():
    """
    检查并安装必要的依赖包。
    使用当前运行的 Python 解释器（PyMOL 环境）安装。
    """
    required_packages = [
        ("openai", "openai>=1.0.0"),
        ("aiohttp", "aiohttp>=3.8.0"),
    ]
    
    missing_packages = []
    for module_name, package_spec in required_packages:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_packages.append(package_spec)
    
    if missing_packages:
        python_executable = sys.executable
        print(f"[PyMOL AI Assistant] 检测到缺失依赖，正在安装: {missing_packages}")
        print(f"[PyMOL AI Assistant] 使用 Python: {python_executable}")
        
        try:
            # 使用 subprocess.run 替代 check_call 以获得更好的错误输出
            result = subprocess.run(
                [python_executable, "-m", "pip", "install"] + missing_packages,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("[PyMOL AI Assistant] 依赖安装成功！")
                # 重新加载模块路径
                importlib.invalidate_caches()
            else:
                print(f"[PyMOL AI Assistant] 依赖安装失败:")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"[PyMOL AI Assistant] 依赖安装失败: {e}")
            print("[PyMOL AI Assistant] 请手动运行: pip install " + " ".join(missing_packages))
            return False
    
    return True

# 启动时检查依赖
_deps_ok = ensure_dependencies()

def __init_plugin__(app=None):
    """
    PyMOL 插件初始化入口（新版 PyMOL）
    """
    try:
        # 延迟导入以避免依赖问题
        from . import ai_chat_gui
        ai_chat_gui.init_plugin(app)
        print("[PyMOL AI Assistant] 插件加载成功！")
    except Exception as e:
        print(f"[PyMOL AI Assistant] 插件加载失败: {e}")
        import traceback
        traceback.print_exc()

# 兼容旧版 PyMOL 的入口
def __init__(app=None):
    """
    PyMOL 插件初始化入口（旧版 PyMOL）
    """
    __init_plugin__(app)

# 如果直接运行此文件（测试用）
if __name__ == "__main__":
    print("PyMOL AI Assistant Plugin")
    print(f"Version: {__version__}")
    print(f"Plugin Dir: {PLUGIN_DIR}")
    print(f"Dependencies OK: {_deps_ok}")
