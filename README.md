# PyMOL AI Assistant 插件

用人话（自然语言）控制 PyMOL。
![主界面](fig/1.png)

从中你可以看到，我只需要跟他说需求，就可以直接操纵pymol了。

## 代码仓库

本项目同时在 GitHub 和 Gitee 同步维护：

- **GitHub**: https://github.com/Masterchiefm/pymol-ai-assistant
- **Gitee**: https://gitee.com/MasterChiefm/pymol-ai-assistant

**国内用户推荐使用 Gitee 访问，下载速度更快。**

## 功能特性

- 🤖 **AI 对话** - 使用自然语言控制 PyMOL
- 🌊 **流式显示** - 实时显示 AI 思考和输出（合并显示，颜色区分）
- 🔧 **工具调用** - AI 可直接操作 PyMOL（加载结构、设置样式、保存图像等）
- ⚙️ **配置管理** - 支持多 API 配置（SiliconFlow、OpenAI 等），可导入导出
- 📋 **日志系统** - 记录所有对话和工具调用，支持过滤和导出
- 🌐 **双语切换** - 支持中文/英文界面一键切换，自动记忆语言偏好
- 📦 **自动依赖** - 安装时自动检查并安装所需依赖

## 安装方法

### 通过 Plugin Manager 安装

1. 下载最新版本的压缩包：
   - 访问 [Releases 页面](https://github.com/Masterchiefm/pymol-ai-assistant/releases/latest) (GitHub)
   - 或访问 [Releases 页面](https://gitee.com/MasterChiefm/pymol-ai-assistant/releases) (Gitee)
   - 下载 **pymol-ai-assistant.zip**

![如何安装插件](fig/2.png)
2. 打开 PyMOL → Plugin → Plugin Manager
3. 点击 "Install New Plugin"
4. 选择下载的 zip 文件
5. 重启 PyMOL

## 使用方法

1. 启动 PyMOL
2. 菜单栏：Plugin → AI Assistant
3. 首次使用需要配置 API：
   - ![](fig/3.png)
   - 点击 "⚙️ 配置" 按钮（或 "⚙️ Config" 如果是英文界面）
   - 添加你的 API 配置（API URL、Key、模型）
   - 支持 SiliconFlow、OpenAI 等兼容 OpenAI API 的服务

4. （可选）点击 "🌐 English" 按钮可切换为英文界面，语言偏好会自动保存

### API 配置示例

#### SiliconFlow 推荐配置（国内用户推荐使用）

- **API URL**: `https://api.siliconflow.cn/v1`
- **推荐模型**:
  - `Pro/moonshotai/Kimi-K2.5` （综合最佳，**需充值使用**）
  - `Pro/zai-org/GLM-4.7` （**需充值使用**）
  - `deepseek-ai/DeepSeek-V3.2` （免费模型）

**注册指南**：
- 使用邀请链接注册可获得 16 元代金券：https://cloud.siliconflow.cn/i/Su2ao83G
- 也可以直接访问 Kimi 官网购买包月计划

4. 配置完成后，在输入框中输入指令，按 Enter 发送

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
加载 PDB 1ake,选出各个链，上色。半透明显示surface
```
![](fig/4.png)


```
我选中的两个东西之间的距离是多少？给我标出来。
```
![](fig/5.png)
![](fig/6.png)

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
