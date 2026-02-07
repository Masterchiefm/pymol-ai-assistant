# -*- coding: utf-8 -*-
import re

# 读取原文件
with open('tools.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义pymol_do_command的新描述
new_do_command_desc = r'''执行一个或多个 PyMOL 命令。多个命令可以用换行符或分号分隔。适用于快速执行简单命令。

可用命令分类：

【文件加载】
- load [文件名], [对象名], [格式] - 加载本地文件（pdb, cif, mol2, sdf等）
- fetch [PDB码], [对象名] - 从PDB数据库下载结构
- run [脚本文件] - 执行Python脚本
- @ [pml脚本文件] - 执行PyMOL命令脚本

【显示控制】
- show [表示形式], [选择] - 显示指定表示形式
  表示形式: lines, sticks, spheres, surface, mesh, ribbon, cartoon, dots, labels, nonbonded, everything
  示例: show cartoon, chain A
- hide [表示形式], [选择] - 隐藏指定表示形式
  示例: hide sticks, all
- enable [对象名] - 启用对象
- disable [对象名] - 禁用对象

【颜色设置】
- color [颜色], [选择] - 设置选择区域颜色
  颜色: red, green, blue, yellow, cyan, magenta, white, black, gray, orange, purple, pink
  特殊: rainbow（彩虹色）, ss（按二级结构）, by_chain（按链）, by_resi（按残基）, by_element（按元素）
  示例: color red, chain A; color rainbow, all
- bg_color [颜色] - 设置背景颜色
  示例: bg_color white
- set_color [颜色名], [RGB值] - 定义新颜色
  示例: set_color mycolor, [0.5, 0.8, 0.2]

【视图控制】
- zoom [选择], [缓冲], [状态] - 缩放到指定选择
  示例: zoom; zoom chain A, buffer=2
- center [选择] - 将视图中心移动到指定选择
  示例: center chain A
- reset - 重置视图到默认状态
- orient - 沿主轴对齐结构
- clip [near], [far] - 设置裁剪平面
  示例: clip near=-5, far=20

【旋转和移动】
- rotate [轴], [角度], [选择] - 旋转
  轴: x, y, z
  示例: rotate x, 30, chain A
- turn [轴], [角度] - 旋转相机
  示例: turn y, 45
- move [x], [y], [z], [选择] - 移动原子
  示例: move 5, 0, 0, chain A
- translate [x], [y], [z], [选择] - 平移选择
  示例: translate 10, 0, 0, all

【选择操作】
- select [名称], [选择表达式] - 创建命名选择集
  选择表达式语法：
  - chain [链ID]: chain A, chain B
  - resi [残基号]: resi 50, resi 1-100
  - resn [残基名]: resn ASP, resn HIS
  - name [原子名]: name CA, name N+O
  - elem [元素]: elem C, elem O+N
  - byres(选择): 按残基选择
  - bychain(选择): 按链选择
  - within [距离] of [选择]: 在指定距离内
  - around [距离]: 周围指定距离
  - and, or, not: 逻辑运算符
  示例: select active_site, resi 50-60; select heme, resn HEM
- deselect - 取消所有选择
- pop [名称], [源选择] - 遍历选择中的原子

【测量】
- distance [名称], [选择1], [选择2] - 测量距离
  示例: distance d1, /1abc//A/50/CA, /1abc//A/100/CA
- angle [名称], [选择1], [选择2], [选择3] - 测量角度
- dihedral [名称], [选择1], [选择2], [选择3], [选择4] - 测量二面角
- get_distance [选择1], [选择2] - 获取距离值
- get_angle [选择1], [选择2], [选择3] - 获取角度值
- get_dihedral [选择1], [选择2], [选择3], [选择4] - 获取二面角值

【结构操作】
- remove [选择] - 删除原子
  示例: remove water; remove solvent
- delete [对象或选择名] - 删除对象或选择
- alter [选择], [表达式] - 修改原子属性
  示例: alter chain A and resi 50, b=50.0
- alter_state [状态], [选择], [表达式] - 修改指定状态的原子属性
- replace [选择], [残基名] - 替换残基
- attach [片段], [氢] - 添加片段
- h_add [选择] - 添加氢原子
- h_fill [选择] - 填充氢原子
- h_fix [选择] - 修复氢原子
- unbond [选择1], [选择2] - 断开键
- bond [选择1], [选择2] - 创建键
- fuse [选择1], [选择2] - 融合选择

【结构分析】
- dss - 计算二级结构
- identify [选择] - 识别原子
- get_model [选择] - 获取分子模型
- get_extent [选择] - 获取范围
- count_atoms [选择] - 统计原子数
- get_chains [选择] - 获取链列表

【对齐和拟合】
- align [移动], [目标] - 序列/结构对齐
  示例: align 1abc, 2def
- fit [移动], [目标] - 拟合结构
- pair_fit [移动1], [目标1], [移动2], [目标2] - 成对拟合
- rms [选择1], [选择2] - 计算RMSD
- super [选择1], [选择2] - 超级对齐

【渲染和导出】
- ray [宽], [高] - 光线追踪渲染
  示例: ray 1600, 1200
- png [文件名], [dpi], [ray] - 保存PNG图像
  示例: png image.png, dpi=300, ray=1
- save [文件名], [格式], [选择] - 保存结构
  格式: pdb, mae, sdf等
  示例: save output.pdb
- save session [文件名] - 保存会话

【设置】
- set [设置名], [值], [选择] - 设置参数
  常用设置:
  - ray_shadows: on/off - 阴影
  - cartoon_tube_radius: 数值 - 管状半径
  - cartoon_cylindrical_helices: on/off - 圆柱螺旋
  - bg_gradient: on/off, 颜色1, 颜色2 - 背景渐变
  - transparency: 0-1 - 透明度
  - sphere_scale: 数值 - 球体大小
  示例: set ray_shadows, on; set transparency, 0.5
- unset [设置名] - 取消设置

【其他】
- cls - 清屏
- help [命令名] - 显示帮助
- quit - 退出
- refresh - 刷新显示
- rebuild - 重建显示
- stereo on/off - 立体模式
- undo - 撤销
- redo - 重做'''

# 查找并替换pymol_do_command的描述
pattern = r'"name": "pymol_do_command",\s+"description": "([^"]+)",'
if re.search(pattern, content):
    content = re.sub(pattern, f'"name": "pymol_do_command",\n                "description": {new_do_command_desc},', content, count=1)
    print("Successfully replaced pymol_do_command description")
else:
    print("Pattern not found for pymol_do_command")

# 写回文件
with open('tools.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
