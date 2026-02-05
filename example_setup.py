"""
PyMOL Python 脚本示例
用于测试 pymol_run_script 工具

这个脚本演示了如何在 Python 脚本中使用 PyMOL cmd API
"""

from pymol import cmd

# 设置背景
cmd.bg_color("black")

# 设置一些参数
cmd.set("ray_shadows", "on")
cmd.set("cartoon_cylindrical_helices", "on")

print("PyMOL 设置已应用")
