# -*- coding: utf-8 -*-
'''
PyMOL AI Assistant Plugin

Version: 2.2.0
Author: Mo Qiqin
License: MIT

Description:
    An AI-powered assistant plugin for PyMOL that uses tool-calling capabilities
    to control PyMOL through natural language conversations.
    Now powered by LiteLLM for unified access to 100+ LLM providers.
'''

from __future__ import print_function
import sys
import os

# 版本号
__version__ = '3.0.2'

# 获取插件目录
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加插件目录到路径
if PLUGIN_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_DIR)


def check_and_install_dependencies():
    """检查并安装依赖"""
    import subprocess
    import importlib

    # 获取当前Python解释器路径
    python_executable = sys.executable

    # 必需的依赖
    required_packages = {
        'requests': 'requests',
        'PyQt5': 'PyQt5',
        'litellm': 'litellm',
        'json_repair': 'json-repair',
    }

    missing_packages = []

    for package_name, install_name in required_packages.items():
        try:
            importlib.import_module(package_name)
        except ImportError:
            missing_packages.append(install_name)

    if missing_packages:
        print("[PyMOL AI Assistant] 正在安装依赖: {}".format(', '.join(missing_packages)))
        try:
            subprocess.check_call([
                python_executable, '-m', 'pip', 'install',
                '-i', 'http://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple',
                '--trusted-host', 'mirrors.tuna.tsinghua.edu.cn',
                '--user', '--quiet'
            ] + missing_packages)
            print("[PyMOL AI Assistant] 依赖安装成功！")
            # 重新加载以检测新安装的包
            for package_name in required_packages.keys():
                try:
                    if package_name in sys.modules:
                        importlib.reload(sys.modules[package_name])
                    else:
                        importlib.import_module(package_name)
                except:
                    pass
        except Exception as e:
            print("[PyMOL AI Assistant] 依赖安装失败: {}".format(e))
            print("[PyMOL AI Assistant] 请手动安装: pip install {}".format(' '.join(missing_packages)))


# 全局变量存储更新信息
_update_info = {
    'has_update': False,
    'latest_version': '',
    'current_version': __version__,
    'release_info': ''
}

def check_update():
    """检查更新"""
    import threading
    import requests

    def _do_check():
        global _update_info
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(
                "https://gitee.com/api/v5/repos/MasterChiefm/pymol-ai-assistant/releases/latest",
                timeout=3,
                headers=headers
            )
            info = response.json()
            latest_version = info.get("tag_name", "").lstrip('v')
            release_info = info.get("body", "")

            if not latest_version:
                return

            # 只要版本号不同就提示更新
            if latest_version != __version__:
                _update_info['has_update'] = True
                _update_info['latest_version'] = latest_version
                _update_info['release_info'] = release_info
                print("[PyMOL AI Assistant] 发现新版本: v{} (当前: v{})".format(latest_version, __version__))
                print("[PyMOL AI Assistant] 请卸载旧版后安装新版")
                print("[PyMOL AI Assistant] 中文用户: https://gitee.com/MasterChiefm/pymol-ai-assistant/releases")
                print("[PyMOL AI Assistant] English: https://github.com/Masterchiefm/pymol-ai-assistant/releases/latest")
            else:
                print("[PyMOL AI Assistant] 当前已是最新版本 (v{})".format(__version__))

        except requests.RequestException as e:
            print("[PyMOL AI Assistant] 检查更新失败 (网络错误): {}".format(e))
        except Exception as e:
            print("[PyMOL AI Assistant] 检查更新失败: {}".format(e))

    # 在后台线程中检查更新
    thread = threading.Thread(target=_do_check, daemon=True)
    thread.start()

def get_update_info():
    """获取更新信息"""
    return _update_info


# 在导入其他模块前检查依赖
check_and_install_dependencies()

# 检查更新
check_update()

# 导入插件主模块
try:
    from . import main
    from .main import AIAssistantDialog
except ImportError as e:
    print("[PyMOL AI Assistant] 导入失败: {}".format(e))
    raise


# 全局对话框实例
_dialog_instance = None


def show_dialog():
    """显示AI助手对话框"""
    global _dialog_instance

    from pymol.Qt import QtWidgets

    # 获取PyMOL主窗口作为父窗口
    app = QtWidgets.QApplication.instance()
    parent = None

    # 尝试获取PyMOL主窗口
    try:
        from pymol import cmd
        parent = cmd.get_qtwindow()
    except:
        pass

    # 如果对话框已存在，则显示它
    if _dialog_instance is not None:
        try:
            _dialog_instance.show()
            _dialog_instance.raise_()
            _dialog_instance.activateWindow()
            return
        except:
            _dialog_instance = None

    # 创建新对话框
    _dialog_instance = AIAssistantDialog(parent)
    _dialog_instance.show()


def __init_plugin__(app=None):
    """初始化插件 - PyMOL会调用这个函数"""
    from pymol.plugins import addmenuitemqt

    # 添加菜单项
    addmenuitemqt('AI Assistant / AI助手', show_dialog)

    print("[PyMOL AI Assistant] 插件 v{} 已加载。请通过 Plugin > AI Assistant / AI助手 菜单打开。".format(__version__))
