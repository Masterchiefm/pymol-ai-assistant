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

### 方法 1：通过 Plugin Manager 安装（推荐）

1. 下载 `pymol-ai-assistant.zip`
2. 打开 PyMOL → Plugin → Plugin Manager
3. 点击 "Install New Plugin"
4. 选择下载的 zip 文件
5. 重启 PyMOL

### 方法 2：手动安装

如果 Plugin Manager 安装失败，请使用手动安装：

1. 解压 `pymol-ai-assistant.zip`
2. 将解压后的 `pymol-ai-assistant` 文件夹复制到 PyMOL 插件目录：
   - **Windows**: `%USERPROFILE%\AppData\Roaming\PyMOL\startup\`
   - **macOS**: `~/Library/Preferences/PyMOL/startup/`
   - **Linux**: `~/.pymol/startup/`
3. 重启 PyMOL

### 方法 3：使用安装脚本

1. 解压 `pymol-ai-assistant.zip`
2. 在 PyMOL 命令行中运行：
   ```
   run /path/to/pymol-ai-assistant/install.py
   ```
3. 按提示完成安装

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

## 支持的 AI 工具

| 工具名 | 功能 |
|--------|------|
| pymol_fetch | 从 PDB 下载结构 |
| pymol_load | 加载本地文件 |
| pymol_show | 显示表示形式 |
| pymol_hide | 隐藏表示形式 |
| pymol_color | 设置颜色 |
| pymol_bg_color | 设置背景颜色 |
| pymol_zoom | 缩放视图 |
| pymol_rotate | 旋转视图 |
| pymol_select | 创建选择集 |
| pymol_label | 添加标签 |
| pymol_ray | 光线追踪渲染 |
| pymol_png | 保存图像 |
| pymol_get_info | 获取分子信息 |
| pymol_reset | 重置视图 |
| pymol_center | 居中视图 |

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

### v1.0.0
- 初始版本
- 支持 AI 对话和工具调用
- 配置管理和日志系统
- 流式响应显示
- 合并思考与输出显示
