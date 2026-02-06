# PyMOL AI Assistant 插件

[![Version](https://img.shields.io/badge/version-1.4.1-blue.svg)](https://github.com/Masterchiefm/pymol-ai-assistant/releases)
[![Python](https://img.shields.io/badge/python-3.x-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

> **用自然语言控制 PyMOL，让分子可视化变得简单高效。**
> 
> **简体中文**（当前）| [English](README.md)

![主界面](fig/1.png)

如图所示，您只需用日常语言描述需求，AI 即可直接操控 PyMOL 完成复杂的分子可视化任务。

---

## 🌐 代码仓库

本项目同时在 GitHub 和 Gitee 同步维护：

| 平台 | 地址 | 推荐度 |
|------|------|--------|
| **GitHub** | https://github.com/Masterchiefm/pymol-ai-assistant | ⭐ 国际访问 |
| **Gitee** | https://gitee.com/MasterChiefm/pymol-ai-assistant | 🇨🇳 国内推荐 |

> **提示**：国内用户推荐使用 Gitee，下载速度更快更稳定。

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🤖 **AI 对话** | 使用自然语言控制 PyMOL，无需记忆复杂命令 |
| 🌊 **流式显示** | 实时显示 AI 思考过程和输出结果，带颜色区分 |
| 🔧 **工具调用** | AI 可直接操作 PyMOL：加载结构、设置样式、保存图像等 |
| ⚙️ **配置管理** | 支持多 API 配置（SiliconFlow、OpenAI 等），支持导入导出 |
| 📋 **日志系统** | 记录所有对话和工具调用，支持过滤和导出 |
| 🌐 **双语切换** | 支持中文/英文界面一键切换，自动记忆语言偏好 |
| 📜 **对话历史** | 查看完整的对话历史 JSON，便于调试和分析 |
| 📦 **自动依赖** | 安装时自动检查并安装所需依赖 |

---

## 📥 安装方法

### 通过 Plugin Manager 安装

1. **下载插件**
   - GitHub: [Releases 页面](https://github.com/Masterchiefm/pymol-ai-assistant/releases/latest)
   - Gitee: [Releases 页面](https://gitee.com/MasterChiefm/pymol-ai-assistant/releases)
   - 下载 `pymol-ai-assistant.zip`

2. **安装步骤**
   
   ![如何安装插件](fig/2.png)
   
   - 打开 PyMOL → Plugin → Plugin Manager
   - 点击 "Install New Plugin"
   - 选择下载的 zip 文件
   - 重启 PyMOL

---

## 🚀 使用方法

### 快速开始

1. 启动 PyMOL
2. 菜单栏：Plugin → AI Assistant
3. 首次使用配置 API：
   
   ![](fig/3.png)
   
   - 点击 "⚙️ 配置" 按钮（英文界面为 "⚙️ Config"）
   - 添加 API 配置（URL、Key、模型）
   - 支持 SiliconFlow、OpenAI 等兼容 OpenAI API 的服务

4. （可选）点击 "🌐 English" 切换为英文界面，语言偏好自动保存

### API 配置示例

#### SiliconFlow（国内用户推荐）

```yaml
API URL: https://api.siliconflow.cn/v1
推荐模型:
  - Pro/moonshotai/Kimi-K2.5  # 综合最佳，需充值
  - Pro/zai-org/GLM-4.7       # 需充值
  - deepseek-ai/DeepSeek-V3.2 # 免费模型
```

**注册优惠**：
- 使用邀请链接注册可获得 16 元代金券：https://cloud.siliconflow.cn/i/Su2ao83G
- 或直接访问 Kimi 官网购买包月计划

配置完成后，在输入框中输入指令，按 **Enter** 发送即可。

---

## 🖥️ 界面说明

### 标签页布局

| 标签 | 内容 |
|------|------|
| 💬 **AI 对话** | 聊天交互界面 |
| 📋 **日志** | 系统日志和调试信息 |
| 📜 **对话历史** | 查看完整的 chat_history JSON |

### 消息样式

- 👤 **用户消息**：蓝色背景，右侧显示
- 🤖 **AI 消息**：绿色背景，左侧显示
  - 💭 **思考过程**：灰色斜体
  - **正式输出**：正常文本
  - ⚙️ **工具调用**：橙色显示
  - ✓ **工具结果**：绿色/红色状态

---

## 💡 示例指令

### 示例 1：加载并可视化分子
```
加载 PDB 1ake，选出各个链并上色，半透明显示 surface
```
![](fig/4.png)

### 示例 2：测量距离
```
我选中的两个残基之间的距离是多少？给我标出来。
```
![](fig/5.png)
![](fig/6.png)

### 更多示例

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

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## ☕ 支持

如果本项目对您有帮助，欢迎 Star ⭐ 支持！

---

## 📝 特别声明

**本项目代码主要由 AI 模型辅助开发：**
- **Kimi K2.5**（月之暗面）- 核心架构与功能实现
- **GLM-4.7**（智谱 AI）- 代码优化与功能完善

在 AI 的协助下，开发者通过自然语言描述需求，实现了这一强大的 PyMOL 智能化插件。

---

**Made with ❤️ and AI (Kimi K2.5 & GLM-4.7)**
