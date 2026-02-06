# -*- coding: utf-8 -*-
'''
PyMOL AI Assistant Plugin

Version: 1.4.1
Author: Mo Qiqin
License: MIT

Description:
    An AI-powered assistant plugin for PyMOL that uses tool-calling capabilities
    to control PyMOL through natural language conversations.
'''

from __future__ import print_function
import sys
import os

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


# 在导入其他模块前检查依赖
check_and_install_dependencies()

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
    
    print("[PyMOL AI Assistant] 插件已加载。请通过 Plugin > AI Assistant / AI助手 菜单打开。")
