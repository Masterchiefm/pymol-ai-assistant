# -*- coding: utf-8 -*-
"""
PyMOL 工具集

定义 AI 可调用的 PyMOL 操作工具。
这些工具通过 Function Calling 机制被 AI 调用。
支持 LiteLLM 统一接口，兼容 100+ LLM 提供商。
"""

import os
import json
import traceback
import sys
import tempfile
from typing import Dict, List, Any, Optional, Callable
from io import StringIO
from . import logger


def supports_function_calling(model: str) -> bool:
    try:
        import litellm

        return litellm.supports_function_calling(model=model)
    except Exception:
        return True


def supports_parallel_function_calling(model: str) -> bool:
    try:
        import litellm

        return litellm.supports_parallel_function_calling(model=model)
    except Exception:
        return False


DEFAULT_PYMOL_WRITE_SCRIPT_DESCRIPTION = """在系统临时文件夹中创建脚本文件，支持 Python (.py) 和 PyMOL 命令脚本 (.pml) 两种格式。创建后使用 pymol_run_script 执行。

【脚本类型选择】
1. Python 脚本 (.py):
   - 需要执行复杂的 PyMOL 操作
   - 需要使用 Python 的循环、条件判断等编程结构
   - 需要自定义函数进行批量处理
   - 需要从脚本中返回计算结果给 AI（通过 print 输出）

2. PyMOL 命令脚本 (.pml):
   - 快速执行一系列 PyMOL 命令，每行一条命令
   - 不需要复杂的逻辑控制
   - 适合简单的加载、显示、着色、渲染操作

【Python 脚本示例】
```python
from pymol import cmd, stored

# 收集CA原子坐标
stored.ca_coords = []
cmd.iterate("name CA", "stored.ca_coords.append([x,y,z])")

# 输出结果（print 内容会被捕获返回）
print(f"共有 {len(stored.ca_coords)} 个CA原子")
for i, coord in enumerate(stored.ca_coords[:5]):
    print(f"  CA{i+1}: ({coord[0]:.2f}, {coord[1]:.2f}, {coord[2]:.2f})")

# 计算表面积
area = cmd.get_area()
print(f"分子表面积: {area:.2f} Å²")
```

【PyMOL 命令脚本 (.pml) 示例】
```pml
fetch 1ake, protein
show cartoon
color red, chain A
color blue, chain B
dss
zoom
```

【pml 命令完整参考】
文件加载:
- load [文件路径], [对象名], [格式] - 加载本地结构文件（支持 pdb, cif, mol2, sdf, ent 等）
- fetch [PDB码], [对象名] - 从 RCSB PDB 数据库下载结构
- run [脚本.py] - 运行 Python 脚本（等同于 pymol_run_script）
- @ [脚本.pml] - 运行 PyMOL 命令脚本

显示控制:
- show [表示], [选择] - 显示表示形式。表示: lines, sticks, spheres, surface, mesh, ribbon, cartoon, dots, labels, nonbonded, slice, extent
- hide [表示], [选择] - 隐藏表示形式
- enable [对象名] - 启用对象
- disable [对象名] - 禁用对象
- as [表示], [选择] - 设置对象的默认显示方式

颜色设置:
- color [颜色], [选择] - 设置颜色。标准色: red, green, blue, yellow, cyan, magenta, white, black, orange, salmon, lime 等。特殊模式: rainbow, by_chain, by_ss, by_resi, by_b, by_element, atomic
- set_color [名称], [R值, G值, B值] - 定义自定义颜色（RGB 范围 0.0-1.0）
- bg_color [颜色] - 设置背景颜色
- spectrum [属性], [渐变色], [选择] - 按属性渐变着色（如 spectrum b, blue_red, all）
- util.cbc [选择] - 按链着色
- ss [选择] - 按二级结构着色（H=螺旋=黄, S=折叠=蓝, ''=环=白）

视图控制:
- zoom [选择], [缓冲] - 缩放（缓冲单位为埃）
- center [选择] - 将视图中心移动到指定选择
- reset - 重置视图
- orient - 沿主轴对齐结构
- clip [near], [far] - 设置裁剪平面
- origin [选择] - 设置旋转中心

旋转和平移:
- rotate [轴], [角度], [选择] - 旋转（轴: x, y, z）
- turn [轴], [角度] - 旋转相机
- move [x], [y], [z], [选择] - 平移原子
- translate [x], [y], [z] - 平移相机

选择操作:
- select [名称], [选择表达式] - 创建命名选择集
- deselect - 取消所有选择
- remove [名称] - 删除对象或选择集
- 选择表达式语法: chain [链ID], resi [残基号范围], resn [残基名], name [原子名], elem [元素], byres(选择), bychain(选择), within [距离] of (选择), (选择) and/or/not (选择)
- 举例: chain A and resi 50-100, name CA, resn HEM, within 5 of chain B

测量:
- distance [名称], [选择1], [选择2] - 测量距离
- angle [名称], [选择1], [选择2], [选择3] - 测量角度
- dihedral [名称], [选择1], [选择2], [选择3], [选择4] - 测量二面角
- dist_count [选择1], [选择2], [截止距离] - 统计接触原子对数

标签和标注:
- label [选择], "[表达式]" - 添加标签。占位符: %s残基名, %i残基号, %n原子名, %r残基, %a元素, %b B因子, %ID原子ID, %chain链, %q占据率, %e热因子
- pseudoatom [名称], [选择] - 创建伪原子
- h_add [选择] - 添加氢原子
- remove_h [选择] - 删除氢原子

渲染和图像:
- ray [宽], [高] - 光线追踪渲染
- png [文件名], [dpi], [ray] - 保存 PNG 图像（ray=1 会先做光线追踪）
- set ray_trace_mode, [0|1] - 0=普通, 1=扁平莫兰迪风格
- set ray_shadow, [0|1] - 开关阴影
- set ambient, [值] - 环境光强度（0-1，默认 0.15）
- set ray_trace_disco_factor, [值] - 阴影散射因子
- set ray_trace_gain, [值] - 增益
- set antialias, [0|1|2] - 抗锯齿级别
- set opaque_background, [0|1] - 背景透明（用于 PNG）

参数设置:
- set [参数], [值], [选择] - 设置 PyMOL 参数
- set cartoon_cylindrical_helices, on - 圆柱形螺旋
- set cartoon_loop_radius, [值] - 环半径
- set cartoon_oval_width, [值] - 螺旋椭圆宽度
- set transparency, [值] - 透明度（0-1）
- set cartoon_side_chain_helper, [1|0] - 显示侧链辅助线
- set sphere_scale, [值] - 球体缩放
- set stick_radius, [值] - 棍模型半径
- set line_width, [值] - 线宽
- set label_size, [值] - 标签字号
- set defer_updates, [0|1] - 延迟更新（批量操作时设为1加速）
- set valence, [0|1] - 显示化学键价态
- set mesh_width, [值] - 网格宽度

表面相关:
- set surface_quality, [0|1] - 表面质量
- set solvent_radius, [值] - 溶剂探针半径
- get_area - 计算表面积
- isosurface [名称], [地图], [阈值] - 等值面

状态和动画:
- mset [状态范围] - 定义动画状态序列（如 mset 1 x100）
- mplay / mstop - 播放/停止动画
- frame [帧号] - 跳到指定帧

对象操作:
- create [新对象], [源选择] - 从选择创建新对象
- copy [目标], [源] - 复制对象
- split_states [对象] - 按状态拆分对象
- orient [选择] - 沿主轴对齐
- symexp [名称], [来源], [切割], [距离] - 对称扩展
- map_generate [名称], [选择], [分辨率] - 生成电子密度图

【注意事项】
- 脚本保存到系统临时文件夹，文件名包含时间戳
- Python 脚本中的 print 输出会被捕获并返回给 AI
- .pml 脚本中每行一条命令，# 为注释
- .pml 文件不支持变量、循环、条件判断等编程结构
- 创建脚本后必须使用 pymol_run_script 来执行"""

DEFAULT_PYMOL_DO_COMMAND_DESCRIPTION = "执行一个或多个 PyMOL 命令。多个命令可以用换行符或分号分隔。适用于快速执行简单命令。\n\n可用命令分类：\n\n【文件加载】\n- load [文件名], [对象名], [格式] - 加载本地文件（pdb, cif, mol2, sdf等）\n- fetch [PDB码], [对象名] - 从PDB数据库下载结构\n- run [脚本文件] - 执行Python脚本\n- @ [pml脚本文件] - 执行PyMOL命令脚本\n\n【显示控制】\n- show [表示形式], [选择] - 显示指定表示形式\n  表示形式: lines, sticks, spheres, surface, mesh, ribbon, cartoon, dots, labels, nonbonded, everything\n  示例: show cartoon, chain A\n- hide [表示形式], [选择] - 隐藏指定表示形式\n  示例: hide sticks, all\n- enable [对象名] - 启用对象\n- disable [对象名] - 禁用对象\n\n【颜色设置】\n- color [颜色], [选择] - 设置选择区域颜色\n  颜色: red, green, blue, yellow, cyan, magenta, white, black, gray, orange, purple, pink\n  特殊: rainbow（彩虹色）, ss（按二级结构）, by_chain（按链）, by_resi（按残基）, by_element（按元素）\n  示例: color red, chain A; color rainbow, all\n- bg_color [颜色] - 设置背景颜色\n  示例: bg_color white\n- set_color [颜色名], [RGB值] - 定义新颜色\n  示例: set_color mycolor, [0.5, 0.8, 0.2]\n\n【视图控制】\n- zoom [选择], [缓冲], [状态] - 缩放到指定选择\n  示例: zoom; zoom chain A, buffer=2\n- center [选择] - 将视图中心移动到指定选择\n  示例: center chain A\n- reset - 重置视图到默认状态\n- orient - 沿主轴对齐结构\n- clip [near], [far] - 设置裁剪平面\n  示例: clip near=-5, far=20\n\n【旋转和移动】\n- rotate [轴], [角度], [选择] - 旋转\n  轴: x, y, z\n  示例: rotate x, 30, chain A\n- turn [轴], [角度] - 旋转相机\n  示例: turn y, 45\n- move [x], [y], [z], [选择] - 移动原子\n  示例: move 5, 0, 0, chain A\n- translate [x], [y], [z], [选择] - 平移选择\n  示例: translate 10, 0, 0, all\n\n【选择操作】\n- select [名称], [选择表达式] - 创建命名选择集\n  选择表达式语法：\n  - chain [链ID]: chain A, chain B\n  - resi [残基号]: resi 50, resi 1-100\n  - resn [残基名]: resn ASP, resn HIS\n  - name [原子名]: name CA, name N+O\n  - elem [元素]: elem C, elem O+N\n  - byres(选择): 按残基选择\n  - bychain(选择): 按链选择\n  - within [距离] of [选择]: 在指定距离内\n  - around [距离]: 周围指定距离\n  - and, or, not: 逻辑运算符\n  示例: select active_site, resi 50-60; select heme, resn HEM\n- deselect - 取消所有选择\n- pop [名称], [源选择] - 遍历选择中的原子\n\n【测量】\n- distance [名称], [选择1], [选择2] - 测量距离\n  示例: distance d1, /1abc//A/50/CA, /1abc//A/100/CA\n- angle [名称], [选择1], [选择2], [选择3] - 测量角度\n  示例: angle a1, /1abc//A/50/CA, /1abc//A/50/C, /1abc//A/50/N\n- dihedral [名称], [选择1], [选择2], [选择3], [选择4] - 测量二面角\n- get_distance [选择1], [选择2] - 获取距离值\n\n【编辑操作】\n- remove [选择] - 删除选择中的原子\n- create [新对象], [源选择] - 从选择创建新对象\n- copy [目标], [源] - 复制对象\n- split_states [对象] - 按状态拆分\n- h_add [选择] - 加氢\n- remove_h [选择] - 删氢\n- alter [选择], [表达式] - 修改原子属性\n- set_symmetry [对象], [空间群], [a], [b], [c], [alpha], [beta], [gamma]\n\n【设置】\n- set [参数], [值], [选择] - 设置PyMOL参数\n  常用参数: ray_shadows, ray_trace_mode, cartoon_cylindrical_helices,\n  bg_gradient, transparency, sphere_scale, stick_radius, line_width,\n  cartoon_loop_radius, cartoon_oval_width, label_size, antialias,\n  ray_trace_disco_factor, ray_trace_gain, ambient, specular,\n  cartoon_side_chain_helper, surface_quality, valence, mesh_width,\n  defer_updates\n\n【渲染与图像】\n- ray [宽], [高] - 光线追踪渲染\n- png [文件名], [dpi], [ray] - 保存图像\n- isomesh [名称], [地图], [阈值], [选择] - 创建网格面\n- isosurface [名称], [地图], [阈值], [选择] - 创建等值面\n\n【其他】\n- dss [选择] - 二级结构分配\n- smooth [选择], [周期] - 平滑\n- intra_fit [选择], [状态] - 内部叠合\n- fit [移动选择], [目标选择] - 叠合\n- align [移动], [目标] - 序列叠合\n- save [文件名], [选择] - 保存结构"


def get_default_tool_prompts():
    """获取默认工具提示词"""
    return {
        "pymol_do_command": DEFAULT_PYMOL_DO_COMMAND_DESCRIPTION,
        "pymol_write_script": DEFAULT_PYMOL_WRITE_SCRIPT_DESCRIPTION,
    }


def get_tool_definitions(is_vision_model: bool = False, custom_prompts: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """
    获取所有工具的定义（用于 OpenAI Function Calling）

    Args:
        is_vision_model: 是否为视觉模型，如果是则包含截图工具
        custom_prompts: 自定义工具提示词字典 {tool_name: description}
    """
    prompts = custom_prompts or {}
    write_script_desc = prompts.get("pymol_write_script", DEFAULT_PYMOL_WRITE_SCRIPT_DESCRIPTION)
    do_command_desc = prompts.get("pymol_do_command", DEFAULT_PYMOL_DO_COMMAND_DESCRIPTION)

    tools = [
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
                            "description": "PDB ID，如 '1ake', '1abc'",
                        },
                        "name": {
                            "type": "string",
                            "description": "对象名称（可选，默认使用 PDB ID）",
                        },
                    },
                    "required": ["code"],
                },
            },
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
                            "description": "文件路径，如 '/path/to/protein.pdb'",
                        },
                        "name": {"type": "string", "description": "对象名称（可选）"},
                        "format": {
                            "type": "string",
                            "description": "文件格式（可选，如 'pdb', 'cif', 'mol2'，默认自动检测）",
                        },
                    },
                    "required": ["filename"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_write_script",
                "description": write_script_desc,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "脚本代码内容"},
                        "name": {
                            "type": "string",
                            "description": "脚本名称（可选，用于标识，默认使用时间戳）",
                        },
                        "script_type": {
                            "type": "string",
                            "description": "脚本类型: python (默认，Python脚本) 或 pml (PyMOL命令脚本)",
                            "enum": ["python", "pml"],
                            "default": "python",
                        },
                    },
                    "required": ["code"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_run_script",
                "description": """执行脚本文件（支持 .py、.pym、.pml 三种格式）。通常先用 pymol_write_script 创建脚本，再用本工具执行。

【支持的文件类型】
- .py / .pym: Python 脚本，在 PyMOL 命名空间中执行，可使用 cmd、stored 等
- .pml: PyMOL 命令脚本，逐行执行每条 PyMOL 命令

【Python 脚本命名空间选项】
- global (默认): 在 PyMOL 全局命名空间中运行，可访问 cmd、stored 等
- local: 在 PyMOL 局部命名空间中运行
- main: 在 Python 主模块命名空间中运行
- module: 作为独立 Python 模块运行
- private: 私有命名空间，局部变量完全隔离

【输出捕获】
- Python 脚本中的 print 输出会被捕获并返回
- .pml 脚本中 PyMOL 的反馈信息会被捕获并返回
- 执行结果和错误信息都会返回给 AI

【使用流程】
1. 先使用 pymol_write_script 创建脚本文件（返回文件路径）
2. 将返回的 path 传给本工具的 filename 参数执行""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "脚本文件路径（.py、.pym 或 .pml），通常来自 pymol_write_script 返回的 path 字段",
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Python 脚本的命名空间: global(默认), local, main, module, private。仅对 .py/.pym 文件有效",
                            "enum": ["global", "local", "main", "module", "private"],
                            "default": "global",
                        },
                    },
                    "required": ["filename"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_do_command",
                "description": do_command_desc,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commands": {
                            "type": "string",
                            "description": "PyMOL 命令或命令序列，如 'load protein.pdb; show cartoon; color rainbow'",
                        }
                    },
                    "required": ["commands"],
                },
            },
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
                            "default": "all",
                        }
                    },
                    "required": [],
                },
            },
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
                            "default": "sele",
                        },
                        "include_atoms": {
                            "type": "boolean",
                            "description": "是否包含每个原子的详细信息（原子名、元素、坐标等）",
                            "default": False,
                        },
                    },
                    "required": [],
                },
            },
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
                            "default": "sele",
                        }
                    },
                    "required": [],
                },
            },
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
                            "default": "sele",
                        }
                    },
                    "required": [],
                },
            },
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
                            "default": "all",
                        }
                    },
                    "required": [],
                },
            },
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
                            "description": "对象名称（可选，留空则返回所有对象信息）",
                        }
                    },
                    "required": [],
                },
            },
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
                            "description": "第一个选择，如 '/1abc//A/50/CA' 或 'chain A and resi 50 and name CA'",
                        },
                        "selection2": {
                            "type": "string",
                            "description": "第二个选择，如 '/1abc//A/100/CA' 或 'chain A and resi 100 and name CA'",
                        },
                    },
                    "required": ["selection1", "selection2"],
                },
            },
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
                            "description": "第一个原子选择",
                        },
                        "selection2": {
                            "type": "string",
                            "description": "第二个原子选择（角顶点）",
                        },
                        "selection3": {
                            "type": "string",
                            "description": "第三个原子选择",
                        },
                    },
                    "required": ["selection1", "selection2", "selection3"],
                },
            },
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
                            "description": "第一个原子选择",
                        },
                        "selection2": {
                            "type": "string",
                            "description": "第二个原子选择",
                        },
                        "selection3": {
                            "type": "string",
                            "description": "第三个原子选择",
                        },
                        "selection4": {
                            "type": "string",
                            "description": "第四个原子选择",
                        },
                    },
                    "required": [
                        "selection1",
                        "selection2",
                        "selection3",
                        "selection4",
                    ],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_find_contacts",
                "description": "查找两个选择之间的原子接触（距离小于指定阈值）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection1": {"type": "string", "description": "第一个选择"},
                        "selection2": {"type": "string", "description": "第二个选择"},
                        "cutoff": {
                            "type": "number",
                            "description": "距离阈值（埃），默认 4.0",
                            "default": 4.0,
                        },
                        "name": {
                            "type": "string",
                            "description": "创建的接触选择集名称（可选）",
                        },
                    },
                    "required": ["selection1", "selection2"],
                },
            },
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
                            "enum": [
                                "lines",
                                "sticks",
                                "spheres",
                                "surface",
                                "mesh",
                                "ribbon",
                                "cartoon",
                                "dots",
                                "labels",
                                "nonbonded",
                            ],
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all",
                        },
                    },
                    "required": ["representation"],
                },
            },
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
                            "default": "everything",
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_color",
                "description": """设置选择区域的颜色。支持标准颜色名称、灰色阶、特殊着色模式。

【标准颜色】
- 基础色: red, green, blue, yellow, cyan, magenta, white, black
- 红色系: tv_red, raspberry, darksalmon, salmon, deepsalmon, warmpink, firebrick, ruby, chocolate, brown
- 绿色系: tv_green, chartreuse, splitpea, smudge, palegreen, limegreen, lime, limon, forest
- 蓝色系: tv_blue, marine, slate, lightblue, skyblue, purpleblue, deepblue, density
- 黄色系: tv_yellow, paleyellow, yelloworange, wheat, sand
- 品红系: lightmagenta, hotpink, pink, lightpink, dirtyviolet, violet, violetpurple, purple, deeppurple
- 青色系: palecyan, aquamarine, greencyan, teal, deepteal, lightteal
- 橙色系: tv_orange, brightorange, lightorange, olive, deepolive
- 灰色系: gray90, gray80, gray70, gray60, gray50, gray40, gray30, gray20, gray10, grey

【特殊着色模式】
- rainbow: 彩虹渐变色（按原子序号）
- by_element: 按元素类型着色（C灰/H白/N蓝/O红/S黄等）
- by_chain: 按链着色（不同链用不同颜色）
- by_ss: 按二级结构着色（螺旋/折叠/环）
- by_resi: 按残基序号渐变色
- by_b: 按B-factor（温度因子）渐变色

【使用示例】
- color red, all - 全部染成红色
- color rainbow, chain A - 链A彩虹色
- color by_element, all - 按元素着色
- color by_chain, all - 按链着色
- color by_ss, all - 按二级结构着色
- color blue, resi 50-100 - 残基50-100染蓝色""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "string",
                            "description": "颜色名称或特殊着色模式",
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认 all）",
                            "default": "all",
                        },
                    },
                    "required": ["color"],
                },
            },
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
                            "default": "black",
                        }
                    },
                    "required": [],
                },
            },
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
                            "default": "all",
                        },
                        "buffer": {
                            "type": "number",
                            "description": "边界缓冲区（埃）",
                            "default": 0,
                        },
                    },
                    "required": [],
                },
            },
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
                            "enum": ["x", "y", "z"],
                        },
                        "angle": {
                            "type": "number",
                            "description": "旋转角度（度）",
                            "default": 90,
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，默认空表示旋转整个视图）",
                            "default": "",
                        },
                    },
                    "required": ["axis"],
                },
            },
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
                            "description": "选择集名称，如 'sele', 'binding_site'",
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式，如 'chain A', 'resi 1-100', 'name CA', 'resn ASP', 'byresi (name CA within 5 of chain B)'",
                        },
                    },
                    "required": ["name", "selection"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_label",
                "description": "为原子添加标签。支持的占位符: %s(残基名), %i(残基号), %n(原子名), %a(原子元素), %ID(ID), %chain(链), %r(残基), %b(B-factor)等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selection": {"type": "string", "description": "选择表达式"},
                        "expression": {
                            "type": "string",
                            "description": "标签表达式，如 '%s%i'(残基名+残基号), '%n-%r'(原子名-残基), '%a'(元素), '%b'(B-factor), '%B'(B-factor格式化)",
                            "default": "%s%i",
                        },
                    },
                    "required": ["selection"],
                },
            },
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
                            "default": 0,
                        },
                        "height": {
                            "type": "integer",
                            "description": "图像高度（像素，可选）",
                            "default": 0,
                        },
                    },
                    "required": [],
                },
            },
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
                            "description": "保存的文件名，如 'image.png'",
                        },
                        "dpi": {
                            "type": "number",
                            "description": "DPI 设置",
                            "default": 300,
                        },
                        "ray": {
                            "type": "integer",
                            "description": "是否使用光线追踪 (1=yes, 0=no)",
                            "default": 1,
                        },
                    },
                    "required": ["filename"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_reset",
                "description": "重置视图到默认状态。",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
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
                            "default": "all",
                        }
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_remove",
                "description": "删除对象或选择集。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "对象或选择集名称"}
                    },
                    "required": ["name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pymol_set",
                "description": "设置 PyMOL 参数。如 ray_shadows, cartoon_cylindrical_helices, bg_gradient, transparency 等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "setting": {
                            "type": "string",
                            "description": "设置名称，如 'ray_shadows', 'cartoon_cylindrical_helices', 'bg_gradient', 'transparency'",
                        },
                        "value": {
                            "type": "string",
                            "description": "设置值，如 'on', 'off', 'on, blue, white', '1', '0', '0.5'",
                        },
                        "selection": {
                            "type": "string",
                            "description": "选择表达式（可选，用于对象特定设置）",
                            "default": "",
                        },
                    },
                    "required": ["setting", "value"],
                },
            },
        },
    ]

    if is_vision_model:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": "pymol_capture_view",
                    "description": "捕获当前PyMOL视图的截图。返回当前渲染画面的base64编码图片数据，让你能够看到实际的画面效果。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "width": {
                                "type": "integer",
                                "description": "截图宽度（像素），默认800，最大1920",
                                "default": 800,
                            },
                            "height": {
                                "type": "integer",
                                "description": "截图高度（像素），默认600，最大1080",
                                "default": 600,
                            },
                            "ray": {
                                "type": "integer",
                                "description": "是否使用光线追踪渲染（1=是，0=否），默认0",
                                "default": 0,
                            },
                        },
                        "required": [],
                    },
                },
            }
        )

    return tools


class ToolExecutor:
    """工具执行器"""

    def __init__(self):
        self.cmd = None
        self._ensure_cmd()

    def _ensure_cmd(self):
        """确保cmd模块已加载"""
        if self.cmd is None:
            try:
                from pymol import cmd

                self.cmd = cmd
            except ImportError:
                raise RuntimeError("PyMOL cmd模块不可用")

    def _preprocess_command(self, cmd, command: str) -> str:
        """
        预处理 PyMOL 命令，处理特殊颜色模式等

        Args:
            cmd: PyMOL cmd 模块
            command: 原始命令

        Returns:
            处理后的命令
        """
        import re

        command_lower = command.lower().strip()

        color_pattern = r"^color\s+(\S+)\s*,?\s*(.*)$"
        match = re.match(color_pattern, command, re.IGNORECASE)

        if match:
            color_name = match.group(1).lower()
            selection = match.group(2).strip() if match.group(2) else "all"

            if color_name == "rainbow":
                return f"spectrum count, rainbow, {selection}"
            elif color_name == "by_element":
                return f"color atomic, ({selection}) and not elem C; color carbon, elem C and ({selection})"
            elif color_name == "by_chain":
                return f"util.cbc {selection}"
            elif color_name == "by_ss":
                return f"color ss, {selection}"
            elif color_name == "by_resi":
                return f"spectrum count, rainbow, {selection}"
            elif color_name == "by_b":
                return f"spectrum b, blue_red, {selection}"

        return command

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定的 PyMOL 工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            执行结果字典
        """
        # 打印调试信息到 PyMOL 控制台
        print(f"[PyMOL AI Assistant] 执行工具: {tool_name}")
        print(f"[PyMOL AI Assistant] 参数: {json.dumps(arguments, ensure_ascii=False)}")

        # 记录到日志
        logger.logger.info(
            logger.TOOL_CALL,
            f"执行工具: {tool_name}",
            {"tool": tool_name, "params": arguments},
        )

        try:
            from pymol import cmd
        except ImportError:
            error_msg = "无法导入 PyMOL cmd 模块"
            print(f"[PyMOL AI Assistant] 错误: {error_msg}")
            logger.logger.error(logger.ERRORS, error_msg)
            return {"success": False, "message": error_msg}

        try:
            result = self._execute_tool(cmd, tool_name, arguments)

            # 记录成功结果
            logger.logger.info(
                logger.TOOL_CALL,
                f"工具执行成功: {tool_name}",
                {"tool": tool_name, "result": result},
            )
            return result

        except Exception as e:
            error_msg = f"执行出错: {str(e)}"
            tb = traceback.format_exc()
            print(f"[PyMOL AI Assistant] 异常: {error_msg}")
            print(f"[PyMOL AI Assistant] 工具: {tool_name}")
            print(f"[PyMOL AI Assistant] 参数: {arguments}")
            print(f"[PyMOL AI Assistant] Traceback:\n{tb}")

            # 记录错误到日志
            logger.logger.error(
                logger.ERRORS,
                f"工具执行失败: {tool_name} - {error_msg}",
                {"tool": tool_name, "params": arguments, "traceback": tb},
            )

            return {"success": False, "message": error_msg, "error": tb}

    def _execute_tool(
        self, cmd, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """实际执行工具的辅助方法"""
        import tempfile, os, sys

        if tool_name == "pymol_fetch":
            code = arguments.get("code", "")
            name = arguments.get("name", "")
            if not name:
                name = code.lower()

            existing_objects = cmd.get_names("objects")
            if name in existing_objects:
                cmd.delete(name)
                print(f"[PyMOL AI Assistant] 删除已存在的对象: {name}")

            cmd._get_feedback()
            cmd.fetch(code, name)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""

            error_patterns = ["Error:", "error:", "ERROR:", "failed", "Failed"]
            has_error = any(pattern in feedback_text for pattern in error_patterns)

            if has_error:
                return {
                    "success": False,
                    "message": f"加载失败: {feedback_text}",
                    "output": feedback_text,
                }

            return {
                "success": True,
                "message": f"已从 PDB 下载并加载 {code}，对象名为 '{name}'",
                "output": feedback_text,
            }

        elif tool_name == "pymol_load":
            filename = arguments.get("filename", "")
            name = arguments.get("name", "")
            format = arguments.get("format", "")

            cmd._get_feedback()

            try:
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

                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""

                error_patterns = ["Error:", "error:", "ERROR:", "failed", "Failed"]
                has_error = any(pattern in feedback_text for pattern in error_patterns)

                if has_error:
                    return {
                        "success": False,
                        "message": f"加载失败: {feedback_text}",
                        "output": feedback_text,
                    }

                return {
                    "success": True,
                    "message": f"已加载文件: {filename}",
                    "output": feedback_text,
                }
            except Exception as e:
                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""
                return {
                    "success": False,
                    "message": f"加载失败: {str(e)}",
                    "output": feedback_text if feedback_text else str(e),
                }

        elif tool_name == "pymol_write_script":
            code = arguments.get("code", "")
            name = arguments.get("name", "")
            script_type = arguments.get("script_type", "python")

            if not code:
                return {"success": False, "message": "错误: 未指定脚本代码"}

            try:
                import time

                timestamp = int(time.time() * 1000)

                if name:
                    script_name = f"{name}_{timestamp}"
                else:
                    script_name = f"pymol_script_{timestamp}"

                # 根据脚本类型确定文件扩展名
                if script_type == "pml":
                    file_ext = ".pml"
                    type_display = "PyMOL"
                else:
                    file_ext = ".py"
                    type_display = "Python"

                temp_dir = tempfile.gettempdir()
                script_path = os.path.join(temp_dir, f"{script_name}{file_ext}")

                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(code)

                return {
                    "success": True,
                    "message": f"{type_display}脚本已创建: {script_path}",
                    "path": script_path,
                    "filename": script_name + file_ext,
                    "script_type": script_type,
                }
            except Exception as e:
                return {"success": False, "message": f"创建脚本失败: {str(e)}"}

        elif tool_name == "pymol_run_script":
            filename = arguments.get("filename", "")
            namespace = arguments.get("namespace", "global")

            if not filename:
                return {"success": False, "message": "错误: 未指定脚本文件路径"}

            # 扩展路径（支持环境变量）
            expanded_path = os.path.expandvars(filename)
            expanded_path = os.path.expanduser(expanded_path)

            # 如果路径不是绝对路径，尝试在当前工作目录查找
            if not os.path.isabs(expanded_path):
                expanded_path = os.path.abspath(expanded_path)

            if not os.path.exists(expanded_path):
                return {
                    "success": False,
                    "message": f"脚本文件不存在: {filename} (解析后: {expanded_path})",
                }

            # 检查文件扩展名
            _, ext = os.path.splitext(expanded_path.lower())
            if ext not in [".py", ".pym", ".pml"]:
                return {
                    "success": False,
                    "message": f"不支持的脚本类型: {ext}。只支持 .py, .pym 和 .pml 文件",
                }

            # 清除之前的反馈
            cmd._get_feedback()

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_stdout = StringIO()
            captured_stderr = StringIO()

            try:
                sys.stdout = captured_stdout
                sys.stderr = captured_stderr

                if ext == ".pml":
                    with open(expanded_path, "r", encoding="utf-8") as f:
                        pml_content = f.read()
                    cmd.do(pml_content)
                    script_type = "PyMOL"
                else:
                    cmd.run(expanded_path, namespace=namespace)
                    script_type = "Python"

                sys.stdout = old_stdout
                sys.stderr = old_stderr

                stdout_text = captured_stdout.getvalue()
                stderr_text = captured_stderr.getvalue()

                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""

                combined_output = ""
                if stdout_text.strip():
                    combined_output += stdout_text.strip()
                if stderr_text.strip():
                    if combined_output:
                        combined_output += "\n"
                    combined_output += "STDERR: " + stderr_text.strip()
                if feedback_text.strip():
                    if combined_output:
                        combined_output += "\n"
                    combined_output += feedback_text.strip()

                has_error = False
                all_text = combined_output.lower()
                if any(
                    kw in all_text
                    for kw in ["error", "traceback", "exception"]
                ):
                    has_error = True

                if has_error:
                    return {
                        "success": False,
                        "message": f"脚本执行出错: {os.path.basename(filename)}",
                        "output": combined_output,
                        "error": feedback_text[:500] if feedback_text else "",
                    }

                if ext == ".pml":
                    message = f"成功执行 PyMOL 脚本: {os.path.basename(filename)}"
                else:
                    message = f"成功执行 Python 脚本: {os.path.basename(filename)} (namespace: {namespace})"

                return {"success": True, "message": message, "output": combined_output}

            except Exception as e:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

                stdout_text = captured_stdout.getvalue()
                stderr_text = captured_stderr.getvalue()

                combined = ""
                if stdout_text.strip():
                    combined += stdout_text.strip()
                if stderr_text.strip():
                    if combined:
                        combined += "\n"
                    combined += "STDERR: " + stderr_text.strip()

                error_msg = f"执行脚本失败: {str(e)}"
                tb = traceback.format_exc()

                return {
                    "success": False,
                    "message": error_msg,
                    "output": combined if combined else "",
                    "error": tb,
                }

        elif tool_name == "pymol_do_command":
            commands = arguments.get("commands", [])

            if isinstance(commands, str):
                commands = [commands]

            results = []
            has_error = False

            for command in commands:
                command = command.strip()
                if not command:
                    continue

                cmd._get_feedback()

                processed_command = self._preprocess_command(cmd, command)

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                captured_stdout = StringIO()
                captured_stderr = StringIO()
                sys.stdout = captured_stdout
                sys.stderr = captured_stderr

                try:
                    if processed_command != command:
                        for cmd_part in processed_command.split(";"):
                            cmd_part = cmd_part.strip()
                            if cmd_part:
                                cmd.do(cmd_part)
                    else:
                        cmd.do(command)
                except Exception as e:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    stdout_text = captured_stdout.getvalue().strip()
                    stderr_text = captured_stderr.getvalue().strip()
                    has_error = True
                    all_output = str(e)
                    if stdout_text:
                        all_output = stdout_text + "\n" + all_output
                    if stderr_text:
                        all_output += "\n" + stderr_text
                    results.append(
                        {
                            "command": command,
                            "status": "error",
                            "message": all_output,
                            "output": all_output,
                        }
                    )
                    continue

                sys.stdout = old_stdout
                sys.stderr = old_stderr

                stdout_text = captured_stdout.getvalue().strip()
                stderr_text = captured_stderr.getvalue().strip()
                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""

                output_parts = []
                if stdout_text:
                    output_parts.append(stdout_text)
                if feedback_text:
                    output_parts.append(feedback_text)
                if stderr_text:
                    output_parts.append(stderr_text)
                combined = "\n".join(output_parts)

                error_patterns = [
                    "Error:",
                    "error:",
                    "ERROR:",
                    "Traceback",
                    "Exception",
                    "Warning:",
                ]
                has_error_in_output = any(
                    pattern in combined for pattern in error_patterns
                )

                if has_error_in_output:
                    has_error = True
                    results.append(
                        {
                            "command": command,
                            "status": "error",
                            "message": combined,
                            "output": combined,
                        }
                    )
                else:
                    results.append(
                        {
                            "command": command,
                            "status": "success",
                            "message": "命令执行成功",
                            "output": combined,
                        }
                    )

            success_count = sum(1 for r in results if r["status"] == "success")
            error_count = len(results) - success_count

            all_outputs = []
            for r in results:
                if r.get("output"):
                    all_outputs.append(f"[{r['command']}]\n{r['output']}")

            combined_output = "\n".join(all_outputs).strip()

            if error_count > 0:
                error_messages = [
                    f"命令 '{r['command']}': {r['message']}"
                    for r in results
                    if r["status"] == "error"
                ]
                return {
                    "success": False,
                    "message": f"执行完成: {success_count} 个成功, {error_count} 个失败",
                    "details": results,
                    "errors": error_messages,
                    "output": combined_output,
                }
            else:
                return {
                    "success": True,
                    "message": f"成功执行 {success_count} 个命令",
                    "details": results,
                    "output": combined_output,
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
                "selection": selection,
            }

            return {
                "success": True,
                "message": f"分子信息: {atom_count} 个原子, {len(object_list)} 个对象, 链: {chains}",
                "data": info,
            }

        elif tool_name == "pymol_get_selection_details":
            selection = arguments.get("selection", "sele")
            include_atoms = arguments.get("include_atoms", False)

            atom_count = cmd.count_atoms(selection)
            if atom_count == 0:
                return {
                    "success": True,
                    "message": f"选择集 '{selection}' 为空，没有选中任何原子",
                    "data": {"selection": selection, "atom_count": 0, "residues": []},
                }

            # 收集残基信息
            residues = {}
            atoms = []

            def collect_residue_info(
                model, chain, resi, resn, ss, atom_name, atom_elem, atom_b, atom_id
            ):
                key = (model, chain, resi, resn)
                if key not in residues:
                    residues[key] = {
                        "model": model,
                        "chain": chain,
                        "residue_number": resi,
                        "residue_name": resn,
                        "secondary_structure": ss,
                        "atom_count": 0,
                        "atoms": [],
                    }
                residues[key]["atom_count"] += 1
                residues[key]["atoms"].append(
                    {
                        "name": atom_name,
                        "element": atom_elem,
                        "b_factor": atom_b,
                        "id": atom_id,
                    }
                )

                if include_atoms:
                    atoms.append(
                        {
                            "model": model,
                            "chain": chain,
                            "residue_number": resi,
                            "residue_name": resn,
                            "atom_name": atom_name,
                            "element": atom_elem,
                            "b_factor": atom_b,
                            "id": atom_id,
                        }
                    )

            # 获取原子详细信息
            cmd.iterate(
                selection,
                "collect_residue_info(model, chain, resi, resn, ss, name, elem, b, ID)",
                space={"collect_residue_info": collect_residue_info},
            )

            # 获取坐标信息（如果需要）
            if include_atoms:
                for i, atom in enumerate(atoms):
                    coords = cmd.get_coords(
                        f"/{atom['model']}//{atom['chain']}/{atom['residue_number']}/{atom['atom_name']}"
                    )
                    if coords is not None and len(coords) > 0:
                        atom["coordinates"] = coords[0].tolist()

            # 转换为列表
            residue_list = sorted(
                residues.values(),
                key=lambda x: (
                    x["model"],
                    x["chain"],
                    int(x["residue_number"])
                    if x["residue_number"].isdigit()
                    else 999999,
                ),
            )

            result = {
                "selection": selection,
                "atom_count": atom_count,
                "residue_count": len(residue_list),
                "residues": residue_list,
            }

            if include_atoms:
                result["atoms"] = atoms

            message = f"选择集 '{selection}' 包含 {atom_count} 个原子，共 {len(residue_list)} 个残基：\n"
            for res in residue_list:
                ss_map = {"H": "螺旋", "S": "折叠", "L": "环", "": "无"}
                ss_text = ss_map.get(
                    res["secondary_structure"], res["secondary_structure"]
                )
                message += f"  - {res['residue_name']} {res['residue_number']} (链 {res['chain']}, {ss_text}, {res['atom_count']} 原子)\n"

            return {"success": True, "message": message, "data": result}

        elif tool_name == "pymol_get_atom_info":
            selection = arguments.get("selection", "sele")

            atom_count = cmd.count_atoms(selection)
            if atom_count == 0:
                return {
                    "success": True,
                    "message": f"选择 '{selection}' 没有选中任何原子",
                    "data": {"selection": selection, "atoms": []},
                }

            atoms = []

            def collect_atom_info(
                model, chain, resi, resn, ss, name, elem, b, q, ID, type
            ):
                coords = cmd.get_coords(f"/{model}//{chain}/{resi}/{name}")
                coord_list = (
                    coords[0].tolist()
                    if coords is not None and len(coords) > 0
                    else None
                )

                atoms.append(
                    {
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
                        "coordinates": coord_list,
                    }
                )

            cmd.iterate(
                selection,
                "collect_atom_info(model, chain, resi, resn, ss, name, elem, b, q, ID, type)",
                space={"collect_atom_info": collect_atom_info},
            )

            return {
                "success": True,
                "message": f"找到 {atom_count} 个原子",
                "data": {
                    "selection": selection,
                    "atom_count": atom_count,
                    "atoms": atoms,
                },
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
                        "secondary_structure": ss,
                    }

            cmd.iterate_state(
                1,
                selection,
                "collect_res_info(model, chain, resi, resn, ss)",
                space={"collect_res_info": collect_res_info},
            )

            # 计算每个残基的原子数
            for key in residues:
                model, chain, resi, resn = key
                atom_count = cmd.count_atoms(f"/{model}//{chain}/{resi}/")
                residues[key]["atom_count"] = atom_count

            residue_list = sorted(
                residues.values(),
                key=lambda x: (
                    x["model"],
                    x["chain"],
                    int(x["residue_number"])
                    if x["residue_number"].isdigit()
                    else 999999,
                ),
            )

            return {
                "success": True,
                "message": f"找到 {len(residue_list)} 个残基",
                "data": {
                    "selection": selection,
                    "residue_count": len(residue_list),
                    "residues": residue_list,
                },
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
                    cmd.iterate(
                        chain_sel,
                        "collect_res_info(resi, resn)",
                        space={"collect_res_info": collect_res_info},
                    )

                    resi_list = sorted(
                        [k[0] for k in residues.keys()],
                        key=lambda x: int(x) if x.isdigit() else 999999,
                    )

                    if resi_list:
                        resi_min = resi_list[0]
                        resi_max = resi_list[-1]
                    else:
                        resi_min = resi_max = ""
                except:
                    resi_min = resi_max = ""

                chain_info.append(
                    {
                        "chain": chain,
                        "atom_count": atom_count,
                        "residue_range": f"{resi_min}-{resi_max}"
                        if resi_min and resi_max
                        else "",
                        "residue_count": len(residues),
                    }
                )

            return {
                "success": True,
                "message": f"找到 {len(chain_info)} 条链",
                "data": {"chain_count": len(chain_info), "chains": chain_info},
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
                    cmd.iterate(
                        obj,
                        "collect_res(resi, resn, chain)",
                        space={"collect_res": collect_res},
                    )
                except:
                    pass

                object_info.append(
                    {
                        "name": obj,
                        "atom_count": atom_count,
                        "state_count": state_count,
                        "residue_count": len(residues),
                        "chains": chains,
                    }
                )

            return {
                "success": True,
                "message": f"对象信息: {len(object_info)} 个对象",
                "data": {"object_count": len(object_info), "objects": object_info},
            }

        elif tool_name == "pymol_get_distance":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")

            try:
                # 检查是否是对象名
                def is_object_name(s):
                    objects = cmd.get_names("objects")
                    return s in objects

                # 如果是对象名，计算第一个原子之间的距离
                if is_object_name(selection1) and is_object_name(selection2):
                    sel1_first = f"first ({selection1})"
                    sel2_first = f"first ({selection2})"
                    distance = cmd.get_distance(sel1_first, sel2_first)
                    note = "（第一个原子之间的距离）"
                else:
                    distance = cmd.get_distance(selection1, selection2)
                    note = ""

                return {
                    "success": True,
                    "message": f"距离: {distance:.3f} Å{note}",
                    "data": {
                        "selection1": selection1,
                        "selection2": selection2,
                        "distance": distance,
                    },
                }
            except Exception as e:
                return {"success": False, "message": f"计算距离失败: {str(e)}"}

        elif tool_name == "pymol_get_angle":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")
            selection3 = arguments.get("selection3", "")

            try:
                angle = cmd.get_angle(selection1, selection2, selection3)
                return {
                    "success": True,
                    "message": f"角度: {angle:.2f}°",
                    "data": {
                        "selection1": selection1,
                        "selection2": selection2,
                        "selection3": selection3,
                        "angle": angle,
                    },
                }
            except Exception as e:
                return {"success": False, "message": f"计算角度失败: {str(e)}"}

        elif tool_name == "pymol_get_dihedral":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")
            selection3 = arguments.get("selection3", "")
            selection4 = arguments.get("selection4", "")

            try:
                dihedral = cmd.get_dihedral(
                    selection1, selection2, selection3, selection4
                )
                return {
                    "success": True,
                    "message": f"二面角: {dihedral:.2f}°",
                    "data": {
                        "selection1": selection1,
                        "selection2": selection2,
                        "selection3": selection3,
                        "selection4": selection4,
                        "dihedral": dihedral,
                    },
                }
            except Exception as e:
                return {"success": False, "message": f"计算二面角失败: {str(e)}"}

        elif tool_name == "pymol_find_contacts":
            selection1 = arguments.get("selection1", "")
            selection2 = arguments.get("selection2", "")
            cutoff = arguments.get("cutoff", 4.0)
            name = arguments.get("name", "")

            try:
                result = cmd.find_pairs(selection1, selection2, cutoff=cutoff)
                contact_count = len(result)

                if name:
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
                    "data": {
                        "selection1": selection1,
                        "selection2": selection2,
                        "cutoff": cutoff,
                        "contact_count": contact_count,
                        "contacts": result,
                    },
                }
            except Exception as e:
                return {"success": False, "message": f"查找接触失败: {str(e)}"}

        elif tool_name == "pymol_show":
            representation = arguments.get("representation", "")
            selection = arguments.get("selection", "all")
            cmd._get_feedback()
            cmd.show(representation, selection)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"已显示 {representation}，选择: {selection}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_hide":
            representation = arguments.get("representation", "everything")
            selection = arguments.get("selection", "all")
            cmd._get_feedback()
            cmd.hide(representation, selection)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"已隐藏 {representation}，选择: {selection}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_color":
            color = arguments.get("color", "").strip().lower()
            selection = arguments.get("selection", "all")

            if not color:
                return {"success": False, "message": "错误: 未指定颜色"}

            cmd._get_feedback()

            try:
                # 特殊着色模式
                if color == "rainbow":
                    cmd.spectrum("count", "rainbow", selection)

                elif color == "by_element":
                    cmd.color("atomic", selection)

                elif color == "by_chain":
                    cmd.util.cbc(selection)

                elif color == "by_ss":
                    cmd.color("ss", selection)

                elif color == "by_resi":
                    cmd.spectrum("count", "rainbow", selection)

                elif color == "by_b":
                    cmd.spectrum("b", "blue_red", selection)

                else:
                    valid_colors = [
                        "red",
                        "green",
                        "blue",
                        "yellow",
                        "cyan",
                        "magenta",
                        "white",
                        "black",
                        "tv_red",
                        "raspberry",
                        "darksalmon",
                        "salmon",
                        "deepsalmon",
                        "warmpink",
                        "firebrick",
                        "ruby",
                        "chocolate",
                        "brown",
                        "tv_green",
                        "chartreuse",
                        "splitpea",
                        "smudge",
                        "palegreen",
                        "limegreen",
                        "lime",
                        "limon",
                        "forest",
                        "tv_blue",
                        "marine",
                        "slate",
                        "lightblue",
                        "skyblue",
                        "purpleblue",
                        "deepblue",
                        "density",
                        "tv_yellow",
                        "paleyellow",
                        "yelloworange",
                        "wheat",
                        "sand",
                        "lightmagenta",
                        "hotpink",
                        "pink",
                        "lightpink",
                        "dirtyviolet",
                        "violet",
                        "violetpurple",
                        "purple",
                        "deeppurple",
                        "palecyan",
                        "aquamarine",
                        "greencyan",
                        "teal",
                        "deepteal",
                        "lightteal",
                        "tv_orange",
                        "brightorange",
                        "lightorange",
                        "olive",
                        "deepolive",
                        "gray",
                        "grey",
                        "gray90",
                        "gray80",
                        "gray70",
                        "gray60",
                        "gray50",
                        "gray40",
                        "gray30",
                        "gray20",
                        "gray10",
                        "orange",
                        "pink",
                        "violet",
                        "brown",
                        "wheat",
                        "slate",
                        "salmon",
                        "atomic",
                        "auto",
                        "default",
                        "current",
                    ]

                    if color not in valid_colors:
                        color_aliases = {
                            "gray": "grey",
                            "grey": "gray",
                        }
                        if color in color_aliases:
                            color = color_aliases[color]

                    cmd.color(color, selection)

                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""

                error_patterns = ["Error:", "error:", "ERROR:", "Unknown color"]
                has_error = any(pattern in feedback_text for pattern in error_patterns)

                if has_error:
                    return {
                        "success": False,
                        "message": f"着色失败: {feedback_text}",
                        "output": feedback_text,
                    }

                return {
                    "success": True,
                    "message": f"已将 '{selection}' 设置为 '{color}' 颜色",
                    "output": feedback_text,
                }

            except Exception as e:
                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""
                return {
                    "success": False,
                    "message": f"着色失败: {str(e)}",
                    "output": feedback_text if feedback_text else str(e),
                }

        elif tool_name == "pymol_bg_color":
            color = arguments.get("color", "") or "black"
            cmd._get_feedback()
            cmd.bg_color(color)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"背景颜色已设置为 {color}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_zoom":
            selection = arguments.get("selection", "all")
            buffer = arguments.get("buffer", 0)
            cmd._get_feedback()
            cmd.zoom(selection, buffer=buffer)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"视图已缩放到: {selection}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_rotate":
            axis = arguments.get("axis", "")
            angle = arguments.get("angle", 90)
            selection = arguments.get("selection", "")

            cmd._get_feedback()
            if selection:
                cmd.rotate(axis, angle, selection)
            else:
                cmd.rotate(axis, angle)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""

            return {
                "success": True,
                "message": f"已旋转 {axis} 轴 {angle} 度",
                "output": feedback_text,
            }

        elif tool_name == "pymol_select":
            name = arguments.get("name", "")
            selection = arguments.get("selection", "")
            cmd._get_feedback()
            cmd.select(name, selection)
            count = cmd.count_atoms(name)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"已创建选择集 '{name}'，包含 {count} 个原子",
                "output": feedback_text,
            }

        elif tool_name == "pymol_label":
            selection = arguments.get("selection", "")
            expression = arguments.get("expression", "%s%i")
            cmd._get_feedback()
            cmd.label(selection, f'"{expression}"')
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"已为 {selection} 添加标签",
                "output": feedback_text,
            }

        elif tool_name == "pymol_ray":
            width = arguments.get("width", 0)
            height = arguments.get("height", 0)

            cmd._get_feedback()
            if width > 0 and height > 0:
                cmd.ray(width, height)
            else:
                cmd.ray()
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""

            return {
                "success": True,
                "message": "光线追踪渲染完成",
                "output": feedback_text,
            }

        elif tool_name == "pymol_png":
            filename = arguments.get("filename", "")
            dpi = arguments.get("dpi", 300)
            ray = arguments.get("ray", 1)

            cmd._get_feedback()
            cmd.png(filename, dpi=dpi, ray=ray)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"图像已保存到: {filename}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_reset":
            cmd._get_feedback()
            cmd.reset()
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {"success": True, "message": "视图已重置", "output": feedback_text}

        elif tool_name == "pymol_center":
            selection = arguments.get("selection", "all")
            cmd._get_feedback()
            cmd.center(selection)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"视图中心已移动到: {selection}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_remove":
            name = arguments.get("name", "")
            cmd._get_feedback()
            cmd.remove(name)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""
            return {
                "success": True,
                "message": f"已删除对象或选择集: {name}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_set":
            setting = arguments.get("setting", "")
            value = arguments.get("value", "")
            selection = arguments.get("selection", "")

            cmd._get_feedback()
            if selection:
                cmd.set(setting, value, selection)
            else:
                cmd.set(setting, value)
            feedback = cmd._get_feedback()
            feedback_text = "\n".join(feedback) if feedback else ""

            return {
                "success": True,
                "message": f"已设置 {setting} = {value}",
                "output": feedback_text,
            }

        elif tool_name == "pymol_capture_view":
            import base64
            import tempfile
            import os

            width = arguments.get("width", 800)
            height = arguments.get("height", 600)
            ray = arguments.get("ray", 0)

            width = min(max(width, 200), 1920)
            height = min(max(height, 200), 1080)

            try:
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as tmp_file:
                    tmp_filename = tmp_file.name

                cmd._get_feedback()

                if ray == 1:
                    cmd.ray(width, height)

                cmd.png(tmp_filename, width=width, height=height, ray=0)

                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""

                with open(tmp_filename, "rb") as f:
                    image_data = f.read()

                image_base64 = base64.b64encode(image_data).decode("utf-8")

                try:
                    os.unlink(tmp_filename)
                except:
                    pass

                return {
                    "success": True,
                    "message": f"已捕获视图截图 ({width}x{height})",
                    "image_data": image_base64,
                    "width": width,
                    "height": height,
                    "format": "png",
                }

            except Exception as e:
                error_msg = f"捕获视图失败: {str(e)}"
                feedback = cmd._get_feedback()
                feedback_text = "\n".join(feedback) if feedback else ""
                return {"success": False, "message": error_msg, "output": feedback_text}

        else:
            error_msg = f"未知工具: {tool_name}"
            print(f"[PyMOL AI Assistant] 错误: {error_msg}")
            print(
                f"[PyMOL AI Assistant] 可用工具: {[t['function']['name'] for t in get_tool_definitions()]}"
            )
            return {"success": False, "message": error_msg}


# 工具描述导出（兼容旧代码）
TOOLS = get_tool_definitions()

# 全局工具执行器实例
tool_executor = ToolExecutor()
