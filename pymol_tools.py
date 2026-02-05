"""
PyMOL 工具集

定义 AI 可调用的 PyMOL 操作工具。
这些工具通过 Function Calling 机制被 AI 调用。
"""

import os
import json
from typing import Dict, List, Any, Optional, Callable


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    获取所有工具的定义（用于 OpenAI Function Calling）
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "pymol_fetch",
                "description": "从 PDB 数据库下载并加载分子结构。支持 PDB ID（如 1ake）或 mmCIF 格式。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "PDB ID，如 '1ake', '1abc'"
                        },
                        "name": {
                            "type": "string",
                            "description": "对象名称（可选，默认使用 PDB ID）"
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_load",
                "description": "从本地文件加载分子结构。支持 PDB、mmCIF、MOL2 等格式。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "文件路径，如 '/path/to/protein.pdb'"
                        },
                        "name": {
                            "type": "string",
                            "description": "对象名称（可选）"
                        },
                        "format": {
                            "type": "string",
                            "description": "文件格式（可选，如 'pdb', 'cif', 'mol2'，默认自动检测）"
                        }
                    },
                    "required": ["filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_run_script",
                "description": "执行 Python 脚本文件（.py 或 .pym）。脚本可以访问 PyMOL cmd API。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Python 脚本文件路径"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "命名空间: global（全局）, local（局部）, main（主模块）, module（模块）, private（私有）",
                            "enum": ["global", "local", "main", "module", "private"],
                            "default": "global"
                        }
                    },
                    "required": ["filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_run_pml",
                "description": "执行 PyMOL 脚本文件（.pml）。这是 PyMOL 的命令脚本格式。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "PyMOL 脚本文件路径（.pml）"
                        }
                    },
                    "required": ["filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_do_command",
                "description": "执行一个或多个 PyMOL 命令。多个命令可以用换行符分隔。适用于快速执行简单命令。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commands": {
                            "type": "string",
                            "description": "PyMOL 命令或命令序列，如 'load protein.pdb; show cartoon; color rainbow'"
                        }
                    },
                    "required": ["commands"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_show",
                "description": "显示指定表示形式（representation）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "representation": {
                            "type": "string",
                            "description": "表示形式: lines, sticks, spheres, surface, mesh, ribbon, cartoon, dots, labels, nonbonded",
                            "enum": ["lines", "sticks", "spheres", "surface", "mesh", "ribbon", "cartoon", "dots", "labels", "nonbonded"]
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all"
                        }
                    },
                    "required": ["representation"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_hide",
                "description": "隐藏指定表示形式或所有表示。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "representation": {
                            "type": "string",
                            "description": "表示形式（可选，默认 everything）",
                            "default": "everything"
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_color",
                "description": "设置选择区域的颜色。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "string",
                            "description": "颜色名称: red, green, blue, yellow, cyan, magenta, white, black, gray, orange, purple, pink, wheat, paleyellow, lightblue, salmon, lime, slate, hotpink, yelloworange, violet, grey, brown, or special: rainbow, by_element, by_chain, by_ss, by_resi"
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all"
                        }
                    },
                    "required": ["color"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_bg_color",
                "description": "设置背景颜色。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "string",
                            "description": "颜色名称: black, white, gray, grey, red, green, blue, yellow, cyan, magenta, orange",
                            "default": "black"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_zoom",
                "description": "缩放视图到指定选择。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all"
                        },
                        "buffer": {
                            "type": "number",
                            "description": "边界缓冲区（埃）",
                            "default": 0
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_rotate",
                "description": "旋转视图或选择。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "axis": {
                            "type": "string",
                            "description": "旋转轴: x, y, z",
                            "enum": ["x", "y", "z"]
                        },
                        "angle": {
                            "type": "number",
                            "description": "旋转角度（度）",
                            "default": 90
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认空表示旋转整个视图）",
                            "default": ""
                        }
                    },
                    "required": ["axis"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_select",
                "description": "创建命名的选择集。选择表达式语法：chain A, resi 1-100, name CA, resn ASP, elem C等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "选择集名称，如 'sele', 'binding_site'"
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式，如 'chain A', 'resi 1-100', 'name CA', 'resn ASP', 'byresi (name CA within 5 of chain B)'"
                        }
                    },
                    "required": ["name", "selection"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_label",
                "description": "为原子添加标签。支持的占位符: %s(残基名), %i(残基号), %n(原子名), %a(原子元素), %ID(ID), %chain(链), %r(残基), %b(B-factor)等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式"
                        },
                        "expression": {
                            "type": "string",
                            "description": "标签表达式，如 '%s%i'(残基名+残基号), '%n-%r'(原子名-残基), '%a'(元素), '%b'(B-factor), '%B'(B-factor格式化)",
                            "default": "%s%i"
                        }
                    },
                    "required": ["selection"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_ray",
                "description": "使用光线追踪渲染高质量图像。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "width": {
                            "type": "integer",
                            "description": "图像宽度（像素，可选）",
                            "default": 0
                        },
                        "height": {
                            "type": "integer",
                            "description": "图像高度（像素，可选）",
                            "default": 0
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_png",
                "description": "保存当前视图为 PNG 图像。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "保存的文件名，如 'image.png'"
                        },
                        "dpi": {
                            "type": "number",
                            "description": "DPI 设置",
                            "default": 300
                        },
                        "ray": {
                            "type": "integer",
                            "description": "是否使用光线追踪 (1=yes, 0=no)",
                            "default": 1
                        }
                    },
                    "required": ["filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_get_info",
                "description": "获取当前加载分子的信息。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_reset",
                "description": "重置视图到默认状态。",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_center",
                "description": "将视图中心移动到指定选择。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_remove",
                "description": "删除对象或选择集。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "对象或选择集名称"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_set",
                "description": "设置 PyMOL 参数。如 ray_shadows, cartoon_cylindrical_helices, bg_gradient 等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "setting": {
                            "type": "string",
                            "description": "设置名称，如 'ray_shadows', 'cartoon_cylindrical_helices', 'bg_gradient'"
                        },
                        "value": {
                            "type": "string",
                            "description": "设置值，如 'on', 'off', 'on, blue, white', '1', '0'"
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，用于对象特定设置）",
                            "default": ""
                        }
                    },
                    "required": ["setting", "value"]
                }
            }
        }
    ]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行指定的 PyMOL 工具

    Args:
        tool_name: 工具名称
        arguments: 工具参数

    Returns:
        执行结果字典
    """
    try:
        from pymol import cmd
    except ImportError:
        return {
            "success": False,
            "message": "无法导入 PyMOL cmd 模块"
        }

    try:
        if tool_name == "pymol_fetch":
            code = arguments.get("code", "")
            name = arguments.get("name", "")
            if not name:
                name = code.lower()
            cmd.fetch(code, name)
            return {
                "success": True,
                "message": f"已从 PDB 下载并加载 {code}，对象名为 '{name}'"
            }

        elif tool_name == "pymol_load":
            filename = arguments.get("filename", "")
            name = arguments.get("name", "")
            format = arguments.get("format", "")

            if name:
                if format:
                    cmd.load(filename, name, format=format)
                else:
                    cmd.load(filename, name)
            else:
                if format:
                    cmd.load(filename, format=format)
                else:
                    cmd.load(filename)
            return {
                "success": True,
                "message": f"已加载文件: {filename}"
            }

        elif tool_name == "pymol_run_script":
            filename = arguments.get("filename", "")
            namespace = arguments.get("namespace", "global")

            if not os.path.exists(filename):
                return {
                    "success": False,
                    "message": f"脚本文件不存在: {filename}"
                }

            cmd.run(filename, namespace=namespace)
            return {
                "success": True,
                "message": f"已执行 Python 脚本: {filename} (namespace: {namespace})"
            }

        elif tool_name == "pymol_run_pml":
            filename = arguments.get("filename", "")

            if not os.path.exists(filename):
                return {
                    "success": False,
                    "message": f"脚本文件不存在: {filename}"
                }

            # 使用 @ 命令执行 .pml 文件
            cmd.do(f"@{filename}")
            return {
                "success": True,
                "message": f"已执行 PyMOL 脚本: {filename}"
            }

        elif tool_name == "pymol_do_command":
            commands = arguments.get("commands", "")
            cmd.do(commands)
            return {
                "success": True,
                "message": f"已执行命令: {commands[:100]}{'...' if len(commands) > 100 else ''}"
            }

        elif tool_name == "pymol_show":
            representation = arguments.get("representation", "")
            selection = arguments.get("selection", "all")
            cmd.show(representation, selection)
            return {
                "success": True,
                "message": f"已显示 {representation}，选择: {selection}"
            }

        elif tool_name == "pymol_hide":
            representation = arguments.get("representation", "everything")
            selection = arguments.get("selection", "all")
            cmd.hide(representation, selection)
            return {
                "success": True,
                "message": f"已隐藏 {representation}，选择: {selection}"
            }

        elif tool_name == "pymol_color":
            color = arguments.get("color", "")
            selection = arguments.get("selection", "all")

            # 特殊颜色方案
            if color == "rainbow":
                cmd.spectrum(selection)
            elif color == "by_element":
                cmd.color("atomic", selection)
            elif color == "by_chain":
                cmd.util.cbc(selection)  # color by chain
            elif color == "by_ss":
                cmd.color("ss", selection)
            elif color == "by_resi":
                cmd.spectrum("count", selection=selection)
            else:
                cmd.color(color, selection)

            return {
                "success": True,
                "message": f"已将 {selection} 设置为 {color} 颜色"
            }

        elif tool_name == "pymol_bg_color":
            color = arguments.get("color", "black")
            cmd.bg_color(color)
            return {
                "success": True,
                "message": f"背景颜色已设置为 {color}"
            }

        elif tool_name == "pymol_zoom":
            selection = arguments.get("selection", "all")
            buffer = arguments.get("buffer", 0)
            cmd.zoom(selection, buffer=buffer)
            return {
                "success": True,
                "message": f"视图已缩放到: {selection}"
            }

        elif tool_name == "pymol_rotate":
            axis = arguments.get("axis", "")
            angle = arguments.get("angle", 90)
            selection = arguments.get("selection", "")

            if selection:
                cmd.rotate(axis, angle, selection)
            else:
                cmd.rotate(axis, angle)

            return {
                "success": True,
                "message": f"已旋转 {axis} 轴 {angle} 度"
            }

        elif tool_name == "pymol_select":
            name = arguments.get("name", "")
            selection = arguments.get("selection", "")
            cmd.select(name, selection)
            count = cmd.count_atoms(name)
            return {
                "success": True,
                "message": f"已创建选择集 '{name}'，包含 {count} 个原子"
            }

        elif tool_name == "pymol_label":
            selection = arguments.get("selection", "")
            expression = arguments.get("expression", "%s%i")
            cmd.label(selection, f'"{expression}"')
            return {
                "success": True,
                "message": f"已为 {selection} 添加标签"
            }

        elif tool_name == "pymol_ray":
            width = arguments.get("width", 0)
            height = arguments.get("height", 0)

            if width > 0 and height > 0:
                cmd.ray(width, height)
            else:
                cmd.ray()

            return {
                "success": True,
                "message": "光线追踪渲染完成"
            }

        elif tool_name == "pymol_png":
            filename = arguments.get("filename", "")
            dpi = arguments.get("dpi", 300)
            ray = arguments.get("ray", 1)

            cmd.png(filename, dpi=dpi, ray=ray)
            return {
                "success": True,
                "message": f"图像已保存到: {filename}"
            }

        elif tool_name == "pymol_get_info":
            selection = arguments.get("selection", "all")

            # 获取信息
            atom_count = cmd.count_atoms(selection)
            object_list = cmd.get_object_list(selection) or []

            # 尝试获取链信息
            try:
                chains = cmd.get_chains(selection) or []
            except:
                chains = []

            # 尝试获取残基信息
            try:
                resn_list = []
                for obj in object_list:
                    cmd.iterate(f"{obj} and ({selection})", "resn_list.append((model, chain, resi, resn))",
                                space={'resn_list': resn_list})
            except:
                resn_list = []

            info = {
                "atom_count": atom_count,
                "object_list": object_list,
                "chains": chains,
                "selection": selection
            }

            return {
                "success": True,
                "message": f"分子信息: {atom_count} 个原子, {len(object_list)} 个对象, 链: {chains}",
                "data": info
            }

        elif tool_name == "pymol_reset":
            cmd.reset()
            return {
                "success": True,
                "message": "视图已重置"
            }

        elif tool_name == "pymol_center":
            selection = arguments.get("selection", "all")
            cmd.center(selection)
            return {
                "success": True,
                "message": f"视图中心已移动到: {selection}"
            }

        elif tool_name == "pymol_remove":
            name = arguments.get("name", "")
            cmd.remove(name)
            return {
                "success": True,
                "message": f"已删除对象或选择集: {name}"
            }

        elif tool_name == "pymol_set":
            setting = arguments.get("setting", "")
            value = arguments.get("value", "")
            selection = arguments.get("selection", "")

            if selection:
                cmd.set(setting, value, selection)
            else:
                cmd.set(setting, value)

            return {
                "success": True,
                "message": f"已设置 {setting} = {value}"
            }

        else:
            return {
                "success": False,
                "message": f"未知工具: {tool_name}"
            }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"执行出错: {str(e)}",
            "error": traceback.format_exc()
        }
