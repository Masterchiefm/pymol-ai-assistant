# PyMOL AI Assistant 插件

通过 AI 工具技能控制 PyMOL 分子可视化软件。

## 功能特性

- 🤖 **AI 对话** - 使用自然语言控制 PyMOL
- 🌊 **流式显示** - 实时显示 AI 思考和输出（合并显示，颜色区分）
- 🔧 **工具调用** - AI 可直接操作 PyMOL（加载结构、设置样式、保存图像等）
- ⚙️ **配置管理** - 支持多 API 配置（SiliconFlow、OpenAI 等），可导入导出
- 📋 **日志系统** - 记录所有对话和工具调用，支持过滤和导出
- 📦 **自动依赖** - 安装时自动检查并安装所需依赖

## 安装方法

### 通过 Plugin Manager 安装

1. 下载最新版本的源码压缩包：
   - 访问 [Releases 页面](https://github.com/Masterchiefm/pymol-ai-assistant/releases/latest)
   - 下载 **Source code (zip)**（不是 Assets 下的文件）
2. 打开 PyMOL → Plugin → Plugin Manager
3. 点击 "Install New Plugin"
4. 选择下载的 zip 文件
5. 重启 PyMOL

## 使用方法

1. 启动 PyMOL
2. 菜单栏：Plugin → AI Assistant
3. 首次使用需要配置 API：
   - 点击 "⚙️ 配置" 按钮
   - 添加你的 API 配置（API URL、Key、模型）
   - 支持 SiliconFlow、OpenAI 等兼容 OpenAI API 的服务
4. 在输入框中输入指令，按 Enter 发送

## 界面说明

- **左侧**：聊天区域
  - 👤 **用户消息**：蓝色背景，右侧显示
  - 🤖 **AI 消息**：绿色背景，左侧显示
    - 💭 **思考过程**：灰色斜体显示
    - **正式输出**：正常黑色文本
    - ⚙️ **工具调用**：橙色显示
    - ✓ **工具结果**：绿色/红色显示
  
- **右侧**：工具调用和日志面板
  - 🔧 **工具调用**：显示所有工具调用和结果
  - 📋 **日志**：系统日志和过滤功能

## 示例指令

```
加载 PDB 1ake
```

```
显示为 cartoon 样式，用 rainbow 着色
```

```
旋转视图 90 度，然后保存为图片
```

```
创建一个选择集，选中 chain A 的所有原子
```

```
执行 PyMOL 脚本 /path/to/script.pml
```

```
运行命令：load 1ake; show cartoon; color chain
```

```
加载并运行 Python 脚本 /path/to/setup.py
```

## 支持的 AI 工具

### 结构加载与脚本执行
| 工具名 | 功能 |
|--------|------|
| pymol_fetch | 从 PDB 下载结构 |
| pymol_load | 加载本地文件 |
| pymol_run_script | 执行 Python 脚本（.py/.pym） |
| pymol_run_pml | 执行 PyMOL 脚本（.pml） |
| pymol_do_command | 执行 PyMOL 命令 |

### 信息查询
| 工具名 | 功能 |
|--------|------|
| pymol_get_info | 获取基本信息（原子数、对象、链） |
| pymol_get_selection_details | 获取选择集详细信息（残基列表、原子数） |
| pymol_get_atom_info | 获取原子详细信息（坐标、B因子、元素等） |
| pymol_get_residue_info | 获取残基详细信息（残基名、编号、二级结构） |
| pymol_get_chain_info | 获取链详细信息（残基范围、原子数） |
| pymol_get_object_info | 获取对象详细信息（状态数、残基数） |
| pymol_get_distance | 计算两个选择之间的距离 |
| pymol_get_angle | 计算三个原子之间的角度 |
| pymol_get_dihedral | 计算四个原子之间的二面角 |
| pymol_find_contacts | 查找原子接触（距离小于阈值） |

### 显示与操作
| 工具名 | 功能 |
|--------|------|
| pymol_show | 显示表示形式 |
| pymol_hide | 隐藏表示形式 |
| pymol_color | 设置颜色 |
| pymol_bg_color | 设置背景颜色 |
| pymol_zoom | 缩放视图 |
| pymol_rotate | 旋转视图 |
| pymol_select | 创建选择集 |
| pymol_label | 添加标签 |
| pymol_reset | 重置视图 |
| pymol_center | 居中视图 |
| pymol_remove | 删除对象或选择集 |
| pymol_set | 设置 PyMOL 参数 |

### 图像导出
| 工具名 | 功能 |
|--------|------|
| pymol_ray | 光线追踪渲染 |
| pymol_png | 保存图像 |

## 默认配置

插件预置了 SiliconFlow 和 OpenAI 的默认配置：

- **SiliconFlow**
  - API URL: `https://api.siliconflow.cn/v1`
  - 模型: `Pro/moonshotai/Kimi-K2.5`

- **OpenAI**
  - API URL: `https://api.openai.com/v1`
  - 模型: `gpt-4o`

## 依赖项

插件会自动安装以下依赖（如果未安装）：
- `openai>=1.0.0`
- `aiohttp>=3.8.0`

手动安装依赖：
```bash
pip install openai>=1.0.0 aiohttp>=3.8.0
```

## 配置文件

配置文件保存在用户目录下：
- **Windows**: `%USERPROFILE%\.pymol_ai_assistant\config.json`
- **macOS/Linux**: `~/.pymol_ai_assistant/config.json`

日志文件保存在：
- **Windows**: `%USERPROFILE%\.pymol_ai_assistant\logs\`
- **macOS/Linux**: `~/.pymol_ai_assistant/logs/`

## 故障排除

### 安装时提示 "Missing __init__.py"

这是 PyMOL Plugin Manager 的一个已知问题。请使用**手动安装**方法：
1. 解压 zip 文件
2. 将 `pymol-ai-assistant` 文件夹复制到 PyMOL 的 `startup` 目录
3. 重启 PyMOL

### 插件加载失败

1. 检查 PyMOL 版本是否支持 Qt 界面
2. 查看 PyMOL 控制台输出的错误信息
3. 确保已安装依赖：`pip install openai aiohttp`

### 工具调用没有执行

1. 确保使用的是支持 Function Calling 的模型（如 gpt-4o、Kimi-K2.5）
2. 查看工具调用面板中的错误信息
3. 检查日志面板中的详细记录

### API 连接失败

1. 检查 API URL 是否正确
2. 检查 API Key 是否有效
3. 检查网络连接
4. 查看日志面板中的详细错误信息

## 注意事项

1. 首次使用需要配置有效的 API Key
2. 建议使用支持 Function Calling 的模型以获得最佳体验
3. 流式响应需要稳定的网络连接

## 版本历史

### v1.3.1
- 修复 thinking 模式下工具调用报错问题
- 更换为 PyMOL 风格深色主题
- 优化滚动条样式
- 配置项"默认"改为"当前使用"

### v1.3.0
- 优化 AI 流式响应处理

### v1.2.0
- 新增 `pymol_get_selection_details`: 获取选择集详细残基信息
- 新增 `pymol_get_atom_info`: 获取原子详细信息（坐标、B因子、元素等）
- 新增 `pymol_get_residue_info`: 获取残基详细信息
- 新增 `pymol_get_chain_info`: 获取链详细信息（残基范围、原子数）
- 新增 `pymol_get_object_info`: 获取对象详细信息
- 新增 `pymol_get_distance`: 计算距离
- 新增 `pymol_get_angle`: 计算角度
- 新增 `pymol_get_dihedral`: 计算二面角
- 新增 `pymol_find_contacts`: 查找原子接触
- 改进所有信息获取工具返回更详细的数据
- 改进 `pymol_color`: 添加 by_b（按 B因子）颜色方案

### v1.1.0
- 新增脚本执行支持（Python .py/.pym 和 PyMOL .pml）
- 新增 `pymol_do_command` 工具执行 PyMOL 命令
- 新增 `pymol_remove` 和 `pymol_set` 工具
- 改进颜色方案支持（by_ss, by_resi）
- 改进标签功能和参数说明
- 根据 PyMOL 源码优化工具实现

### v1.0.0
- 初始版本
- 支持 AI 对话和工具调用
- 配置管理和日志系统
- 流式响应显示
- 合并思考与输出显示
