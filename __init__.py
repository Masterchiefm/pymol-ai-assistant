# -*- coding: utf-8 -*-
"""
PyMOL AI Assistant Plugin

Author: Mo Qiqin
License: MIT

Description:
    An AI-powered assistant plugin for PyMOL that uses tool-calling capabilities
    to control PyMOL through natural language conversations.
    Now powered by LiteLLM for unified access to 100+ LLM providers.
"""

from __future__ import print_function
import sys
import os

import time as _time

# 版本号
__version__ = "3.0.4"

# 获取插件目录
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加插件目录到路径
if PLUGIN_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_DIR)


def check_and_install_dependencies():
    """检查并安装依赖"""
    import subprocess

    python_executable = sys.executable

    required_packages = {
        "requests": "requests",
        "PyQt5": "PyQt5",
        "litellm": "litellm",
        "json_repair": "json-repair",
        "markdown": "markdown",
    }

    missing_packages = [
        install_name
        for package_name, install_name in required_packages.items()
        if package_name not in sys.modules
    ]

    if missing_packages:
        print(
            "[PyMOL AI Assistant] 正在安装依赖: {}".format(", ".join(missing_packages))
        )
        try:
            subprocess.check_call(
                [
                    python_executable,
                    "-m",
                    "pip",
                    "install",
                    "-i",
                    "http://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple",
                    "--trusted-host",
                    "mirrors.tuna.tsinghua.edu.cn",
                    "--user",
                    "--quiet",
                ]
                + missing_packages
            )
            print("[PyMOL AI Assistant] 依赖安装成功！")
        except Exception as e:
            print("[PyMOL AI Assistant] 依赖安装失败: {}".format(e))
            print(
                "[PyMOL AI Assistant] 请手动安装: pip install {}".format(
                    " ".join(missing_packages)
                )
            )


# 全局变量存储更新信息
_update_info = {
    "has_update": False,
    "latest_version": "",
    "current_version": __version__,
    "release_info": "",
}


def check_update():
    """检查更新"""
    import threading
    import requests

    def _do_check():
        global _update_info
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(
                "https://gitee.com/api/v5/repos/MasterChiefm/pymol-ai-assistant/releases/latest",
                timeout=3,
                headers=headers,
            )
            info = response.json()
            latest_version = info.get("tag_name", "").lstrip("v")
            release_info = info.get("body", "")

            if not latest_version:
                return

            # 只要版本号不同就提示更新
            if latest_version != __version__:
                _update_info["has_update"] = True
                _update_info["latest_version"] = latest_version
                _update_info["release_info"] = release_info
                print(
                    "[PyMOL AI Assistant] 发现新版本: v{} (当前: v{})".format(
                        latest_version, __version__
                    )
                )
                print("[PyMOL AI Assistant] 请卸载旧版后安装新版")
                print(
                    "[PyMOL AI Assistant] 中文用户: https://gitee.com/MasterChiefm/pymol-ai-assistant/releases"
                )
                print(
                    "[PyMOL AI Assistant] English: https://github.com/Masterchiefm/pymol-ai-assistant/releases/latest"
                )
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


# 在后台检查依赖（不阻塞启动）
_t0 = _time.time()
import threading as _threading

_dep_thread = _threading.Thread(target=check_and_install_dependencies, daemon=True)
_dep_thread.start()
_t1 = _time.time()
print(
    "[PyMOL AI Assistant] [耗时] check_and_install_dependencies (后台): {:.3f}s".format(
        _t1 - _t0
    )
)

# 检查更新（后台线程）
check_update()

# 全局对话框实例
_dialog_instance = None


def show_dialog():
    """显示AI助手对话框"""
    global _dialog_instance

    import time as _time

    _t0 = _time.time()

    from pymol.Qt import QtWidgets

    _t1 = _time.time()
    print("[PyMOL AI Assistant] [耗时] import pymol.Qt: {:.3f}s".format(_t1 - _t0))

    from . import i18n

    _t2 = _time.time()
    print("[PyMOL AI Assistant] [耗时] import i18n: {:.3f}s".format(_t2 - _t1))

    from . import config

    _t3 = _time.time()
    print("[PyMOL AI Assistant] [耗时] import config: {:.3f}s".format(_t3 - _t2))

    from . import logger

    _t4 = _time.time()
    print("[PyMOL AI Assistant] [耗时] import logger: {:.3f}s".format(_t4 - _t3))

    _t_pre_litellm = _time.time()
    from . import ai_client

    _t5 = _time.time()
    print(
        "[PyMOL AI Assistant] [耗时] import ai_client (含 litellm): {:.3f}s".format(
            _t5 - _t_pre_litellm
        )
    )

    from . import tools

    _t6 = _time.time()
    print(
        "[PyMOL AI Assistant] [耗时] import tools (含 pymol.cmd): {:.3f}s".format(
            _t6 - _t5
        )
    )

    from . import markdown_renderer

    _t7 = _time.time()
    print(
        "[PyMOL AI Assistant] [耗时] import markdown_renderer: {:.3f}s".format(
            _t7 - _t6
        )
    )

    from . import updater

    _t8 = _time.time()
    print("[PyMOL AI Assistant] [耗时] import updater: {:.3f}s".format(_t8 - _t7))

    from .main import AIAssistantDialog

    _t9 = _time.time()
    print("[PyMOL AI Assistant] [耗时] import main: {:.3f}s".format(_t9 - _t8))
    print("[PyMOL AI Assistant] [耗时] 全部导入总计: {:.3f}s".format(_t9 - _t0))

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
    _t_create = _time.time()
    _dialog_instance = AIAssistantDialog(parent)
    _t_done = _time.time()
    print("[PyMOL AI Assistant] [耗时] 创建对话框: {:.3f}s".format(_t_done - _t_create))
    print("[PyMOL AI Assistant] [耗时] show_dialog 总计: {:.3f}s".format(_t_done - _t0))

    _dialog_instance.show()


def __init_plugin__(app=None):
    """初始化插件 - PyMOL会调用这个函数"""
    _t0 = _time.time()
    from pymol.plugins import addmenuitemqt

    _t1 = _time.time()
    print(
        "[PyMOL AI Assistant] [耗时] __init_plugin__ import pymol.plugins: {:.3f}s".format(
            _t1 - _t0
        )
    )

    addmenuitemqt("AI Assistant / AI助手", show_dialog)

    print(
        "[PyMOL AI Assistant] 插件 v{} 已加载。请通过 Plugin > AI Assistant / AI助手 菜单打开。".format(
            __version__
        )
    )
