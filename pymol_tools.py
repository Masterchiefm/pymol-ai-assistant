"""
PyMOL 工具集

定义 AI 可调用的 PyMOL 操作工具。
这些工具通过 Function Calling 机制被 AI 调用。
"""

import os
import json
import traceback
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
                "description": "执行一个或多个 PyMOL 命令。多个命令可以用换行符或分号分隔。适用于快速执行简单命令。",
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
                "name": "pymol_get_info",
                "description": "获取当前加载分子的基本信息，包括原子数、对象列表、链列表。",
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
                "name": "pymol_get_selection_details",
                "description": "获取选择集的详细信息，包括每个残基的名称、编号、链、原子数等。适用于回答'当前选中的是什么氨基酸'之类的问题。默认使用 'sele'（PyMOL 的当前选择集）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 'sele' 即当前选择集）",
                            "default": "sele"
                        },
                        "include_atoms": {
                            "type": "boolean",
                            "description": "是否包含每个原子的详细信息（原子名、元素、坐标等）",
                            "default": false
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_get_atom_info",
                "description": "获取单个或多个原子的详细信息，包括原子名、元素、残基、链、B因子、坐标等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式，如 'sele', 'chain A and resi 50', '/1abc//A/50/CA'",
                            "default": "sele"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_get_residue_info",
                "description": "获取残基的详细信息，包括残基名、残基号、链、二级结构、原子数等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式，如 'sele', 'chain A and resi 50', '/1abc//A/50'",
                            "default": "sele"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_get_chain_info",
                "description": "获取链的详细信息，包括链标识、残基范围、原子数等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {
                            "type": "string",
                            "description": "选择表达式，如 'chain A', 'all', 'sele'",
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
                "name": "pymol_get_object_info",
                "description": "获取对象的详细信息，包括对象名、状态数、原子数、残基数、链等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_name": {
                            "type": "string",
                            "description": "对象名称（可选，留空则返回所有对象信息）"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_get_distance",
                "description": "计算两个选择之间的距离（埃）。返回第一个原子对之间的距离。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection1": {
                            "type": "string",
                            "description": "第一个选择，如 '/1abc//A/50/CA' 或 'chain A and resi 50 and name CA'"
                        },
                        "selection2": {
                            "type": "string",
                            "description": "第二个选择，如 '/1abc//A/100/CA' 或 'chain A and resi 100 and name CA'"
                        }
                    },
                    "required": ["selection1", "selection2"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_get_angle",
                "description": "计算三个原子之间的角度（度）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection1": {
                            "type": "string",
                            "description": "第一个原子选择"
                        },
                        "selection2": {
                            "type": "string",
                            "description": "第二个原子选择（角顶点）"
                        },
                        "selection3": {
                            "type": "string",
                            "description": "第三个原子选择"
                        }
                    },
                    "required": ["selection1", "selection2", "selection3"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_get_dihedral",
                "description": "计算四个原子之间的二面角（度）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection1": {
                            "type": "string",
                            "description": "第一个原子选择"
                        },
                        "selection2": {
                            "type": "string",
                            "description": "第二个原子选择"
                        },
                        "selection3": {
                            "type": "string",
                            "description": "第三个原子选择"
                        },
                        "selection4": {
                            "type": "string",
                            "description": "第四个原子选择"
                        }
                    },
                    "required": ["selection1", "selection2", "selection3", "selection4"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_find_contacts",
                "description": "查找两个选择之间的原子接触（距离小于指定阈值）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection1": {
                            "type": "string",
                            "description": "第一个选择"
                        },
                        "selection2": {
                            "type": "string",
                            "description": "第二个选择"
                        },
                        "cutoff": {
                            "type": "number",
                            "description": "距离阈值（埃），默认 4.0",
                            "default": 4.0
                        },
                        "name": {
                            "type": "string",
                            "description": "创建的接触选择集名称（可选）"
                        }
                    },
                    "required": ["selection1", "selection2"]
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
                            "description": "颜色名称: red, green, blue, yellow, cyan, magenta, white, black, gray, orange, purple, pink, wheat, paleyellow, lightblue, salmon, lime, slate, hotpink, yelloworange, violet, grey, brown, or special: rainbow, by_element, by_chain, by_ss, by_resi, by_b"
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
    # 打印调试信息到 PyMOL 控制台（这样更容易看到）
    print(f"[PyMOL AI Assistant] 执行工具: {tool_name}")
    print(f"[PyMOL AI Assistant] 参数: {json.dumps(arguments, ensure_ascii=False)}")

    try:
        from pymol import cmd
    except ImportError:
        error_msg = "无法导入 PyMOL cmd 模块"
        print(f"[PyMOL AI Assistant] 错误: {error_msg}")
        return {
            "success": False,
            "message": error_msg
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

        elif tool_name == "pymol_get_info":
            selection = arguments.get("selection", "all")

            atom_count = cmd.count_atoms(selection)
            object_list = cmd.get_object_list(selection) or []

            try:
                chains = cmd.get_chains(selection) or []
            except:
                chains = []

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

        elif tool_name == "pymol_get_selection_details":
            selection = arguments.get("selection", "sele")
            include_atoms = arguments.get("include_atoms", False)

            atom_count = cmd.count_atoms(selection)
            if atom_count == 0:
                return {
                    "success": True,
                    "message": f"选择集 '{selection}' 为空，没有选中任何原子",
                    "data": {"selection": selection, "atom_count": 0, "residues": []}
                }

            # 收集残基信息
            residues = {}
            atoms = []

            def collect_residue_info(model, chain, resi, resn, ss, atom_name, atom_elem, atom_b, atom_id):
                key = (model, chain, resi, resn)
                if key not in residues:
                    residues[key] = {
                        "model": model,
                        "chain": chain,
                        "residue_number": resi,
                        "residue_name": resn,
                        "secondary_structure": ss,
                        "atom_count": 0,
                        "atoms": []
                    }
                residues[key]["atom_count"] += 1
                residues[key]["atoms"].append({
                    "name": atom_name,
                    "element": atom_elem,
                    "b_factor": atom_b,
                    "id": atom_id
                })

                if include_atoms:
                    atoms.append({
                        "model": model,
                        "chain": chain,
                        "residue_number": resi,
                        "residue_name": resn,
                        "atom_name": atom_name,
                        "element": atom_elem,
                        "b_factor": atom_b,
                        "id": atom_id
                    })

            # 获取原子详细信息
            cmd.iterate(selection,
                        "collect_residue_info(model, chain, resi, resn, ss, name, elem, b, ID)",
                        space={"collect_residue_info": collect_residue_info})

            # 获取坐标信息（如果需要）
            if include_atoms:
                for i, atom in enumerate(atoms):
                    coords = cmd.get_coords(f"/{atom['model']}//{atom['chain']}/{atom['residue_number']}/{atom['atom_name']}")
                    if coords is not None and len(coords) > 0:
                        atom["coordinates"] = coords[0].tolist()

            # 转换为列表
            residue_list = sorted(residues.values(),
                                key=lambda x: (x["model"], x["chain"], int(x["residue_number"]) if x["residue_number"].isdigit() else 999999))

            result = {
                "selection": selection,
                "atom_count": atom_count,
                "residue_count": len(residue_list),
                "residues": residue_list
            }

            if include_atoms:
                result["atoms"] = atoms

            message = f"选择集 '{selection}' 包含 {atom_count} 个原子，共 {len(residue_list)} 个残基：\n"
            for res in residue_list:
                ss_map = {"H": "螺旋", "S": "折叠", "L": "环", "": "无"}
                ss_text = ss_map.get(res["secondary_structure"], res["secondary_structure"])
                message += f"  - {res['residue_name']} {res['residue_number']} (链 {res['chain']}, {ss_text}, {res['atom_count']} 原子)\n"

            return {
                "success": True,
                "message": message,
                "data": result
            }

        elif tool_name == "pymol_get_atom_info":
            selection = arguments.get("selection", "sele")

            atom_count = cmd.count_atoms(selection)
            if atom_count == 0:
                return {
                    "success": True,
                    "message": f"选择 '{selection}' 没有选中任何原子",
                    "data": {"selection": selection, "atoms": []}
                }

            atoms = []

            def collect_atom_info(model, chain, resi, resn, ss, name, elem, b, q, ID, type):
                coords = cmd.get_coords(f"/{model}//{chain}/{resi}/{name}")
                coord_list = coords[0].tolist() if coords is not None and len(coords) > 0 else None

                atoms.append({
                    "model": model,
                    "chain": chain,
                    "residue_number": resi,
                    "residue_name": resn,
                    "secondary_structure": ss,
                    "atom_name": name,
                    "element": elem,
                    "b_factor": b,
                    "occupancy": q,
                    "id": ID,
                    "type": type,
                    "coordinates": coord_list
                })

            cmd.iterate(selection,
                        "collect_atom_info(model, chain, resi, resn, ss, name, elem, b, q, ID, type)",
                        space={"collect_atom_info": collect_atom_info})

            return {
                "success": True,
                "message": f"找到 {atom_count} 个原子",
                "data": {"selection": selection, "atom_count": atom_count, "atoms": atoms}
            }

        elif tool_name == "pymol_get_residue_info":
            selection = arguments.get("selection", "sele")

            residues = {}

            def collect_res_info(model, chain, resi, resn, ss):
                key = (model, chain, resi, resn)
                if key not in residues:
                    residues[key] = {
                        "model": model,
                        "chain": chain,
                        "residue_number": resi,
                        "residue_name": resn,
                        "secondary_structure": ss
                    }

            cmd.iterate_state(1, selection,
                            "collect_res_info(model, chain, resi, resn, ss)",
                            space={"collect_res_info": collect_res_info})

            # 计算每个残基的原子数
            for key in residues:
                model, chain, resi, resn = key
                atom_count = cmd.count_atoms(f"/{model}//{chain}/{resi}/")
                residues[key]["atom_count"] = atom_count

            residue_list = sorted(residues.values(),
                                key=lambda x: (x["model"], x["chain"], int(x["residue_number"]) if x["residue_number"].isdigit() else 999999))

            return {
                "success": True,
                "message": f"找到 {len(residue_list)} 个残基",
                "data": {"selection": selection, "residue_count": len(residue_list), "residues": residue_list}
            }

        elif tool_name == "pymol_get_chain_info":
            selection = arguments.get("selection", "all")

            try:
                chains = cmd.get_chains(selection) or []
            except:
                chains = []

            chain_info = []

            for chain in chains:
                chain_sel = f"{selection} and chain {chain}"
                atom_count = cmd.count_atoms(chain_sel)

                # 获取残基范围
                residues = {}
                def collect_res_info(resi, resn):
                    residues[(resi, resn)] = True

                try:
                    cmd.iterate(chain_sel, "collect_res_info(resi, resn)",
                               space={"collect_res_info": collect_res_info})

                    resi_list = sorted([k[0] for k in residues.keys()],
                                       key=lambda x: int(x) if x.isdigit() else 999999)

                    if resi_list:
                        resi_min = resi_list[0]
                        resi_max = resi_list[-1]
                    else:
                        resi_min = resi_max = ""
                except:
                    resi_min = resi_max = ""

                chain_info.append({
                    "chain": chain,
                    "atom_count": atom_count,
                    "residue_range": f"{resi_min}-{resi_max}" if resi_min and resi_max else "",
                    "residue_count": len(residues)
                })

            return {
                "success": True,
                "message": f"找到 {len(chain_info)} 条链",
                "data": {"chain_count": len(chain_info), "chains": chain_info}
            }

        elif tool_name == "pymol_get_object_info":
            object_name = arguments.get("object_name", "")

            if object_name:
                objects = [object_name]
            else:
                objects = cmd.get_object_list("all") or []

            object_info = []

            for obj in objects:
                atom_count = cmd.count_atoms(obj)
                state_count = cmd.get_object_state(obj)

                # 获取链信息
                try:
                    chains = cmd.get_chains(obj) or []
                except:
                    chains = []

                # 获取残基数
                residues = set()
                def collect_res(resi, resn, chain):
                    residues.add((resi, resn, chain))

                try:
                    cmd.iterate(obj, "collect_res(resi, resn, chain)",
                               space={"collect_res": collect_res})
                except:
                    pass

                object_info.append({
                    "name": obj,
                    "atom_count": atom_count,
                    "state_count": state_count,
                    "residue_count": len(residues),
                    "chains": chains
                })

            return {
                "success": True,
                "message": f"对象信息: {len(object_info)} 个对象",
                "data": {"object_count": len(object_info), "objects": object_info}
            }

        elif tool_name == "pymol_get_distance":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")

            try:
                distance = cmd.get_distance(selection1, selection2)
                return {
                    "success": True,
                    "message": f"距离: {distance:.3f} Å",
                    "data": {"selection1": selection1, "selection2": selection2, "distance": distance}
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"计算距离失败: {str(e)}"
                }

        elif tool_name == "pymol_get_angle":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")
            selection3 = arguments.get("selection3", "")

            try:
                angle = cmd.get_angle(selection1, selection2, selection3)
                return {
                    "success": True,
                    "message": f"角度: {angle:.2f}°",
                    "data": {"selection1": selection1, "selection2": selection2, "selection3": selection3, "angle": angle}
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"计算角度失败: {str(e)}"
                }

        elif tool_name == "pymol_get_dihedral":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")
            selection3 = arguments.get("selection3", "")
            selection4 = arguments.get("selection4", "")

            try:
                dihedral = cmd.get_dihedral(selection1, selection2, selection3, selection4)
                return {
                    "success": True,
                    "message": f"二面角: {dihedral:.2f}°",
                    "data": {"selection1": selection1, "selection2": selection2, "selection3": selection3,
                            "selection4": selection4, "dihedral": dihedral}
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"计算二面角失败: {str(e)}"
                }

        elif tool_name == "pymol_find_contacts":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")
            cutoff = arguments.get("cutoff", 4.0)
            name = arguments.get("name", "")

            try:
                result = cmd.find_pairs(f"({selection1}) and ({selection2})", cutoff)
                contact_count = len(result)

                if name:
                    # 创建选择集
                    selections = []
                    for pair in result:
                        for atom in pair:
                            selections.append(f"ID {atom[6]}")
                    if selections:
                        sel_expr = " or ".join(selections)
                        cmd.select(name, sel_expr)

                return {
                    "success": True,
                    "message": f"找到 {contact_count} 对接触原子（距离 < {cutoff} Å）",
                    "data": {"selection1": selection1, "selection2": selection2, "cutoff": cutoff,
                            "contact_count": contact_count, "contacts": result}
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"查找接触失败: {str(e)}"
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

            if color == "rainbow":
                cmd.spectrum(selection)
            elif color == "by_element":
                cmd.color("atomic", selection)
            elif color == "by_chain":
                cmd.util.cbc(selection)
            elif color == "by_ss":
                cmd.color("ss", selection)
            elif color == "by_resi":
                cmd.spectrum("count", selection=selection)
            elif color == "by_b":
                cmd.spectrum("b", selection=selection)
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
            error_msg = f"未知工具: {tool_name}"
            print(f"[PyMOL AI Assistant] 错误: {error_msg}")
            print(f"[PyMOL AI Assistant] 可用工具: {[t['function']['name'] for t in get_tool_definitions()]}")
            return {
                "success": False,
                "message": error_msg
            }

    except Exception as e:
        error_msg = f"执行出错: {str(e)}"
        tb = traceback.format_exc()
        print(f"[PyMOL AI Assistant] 异常: {error_msg}")
        print(f"[PyMOL AI Assistant] 工具: {tool_name}")
        print(f"[PyMOL AI Assistant] 参数: {arguments}")
        print(f"[PyMOL AI Assistant] Traceback:\n{tb}")
        return {
            "success": False,
            "message": error_msg,
            "error": tb
        }
