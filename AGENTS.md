# PyMOL AI Assistant Plugin - Agent Guide

## Project Overview

PyMOL AI Assistant 是一个 PyMOL 分子可视化软件的插件，通过 AI 工具技能（Function Calling）实现自然语言控制 PyMOL。

**Version**: 1.2.0  
**Language**: Chinese (Simplified)  
**License**: Not specified

### Core Features

- 🤖 **AI 对话** - 使用自然语言控制 PyMOL
- 🌊 **流式显示** - 实时显示 AI 思考和输出（合并显示，颜色区分）
- 🔧 **工具调用** - AI 可直接操作 PyMOL（加载结构、设置样式、保存图像等）
- ⚙️ **配置管理** - 支持多 API 配置（SiliconFlow、OpenAI 等），可导入导出
- 📋 **日志系统** - 记录所有对话和工具调用，支持过滤和导出
- 📦 **自动依赖** - 安装时自动检查并安装所需依赖

## Technology Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.x |
| Host Application | PyMOL (molecular visualization software) |
| GUI Framework | PyQt5 (via `pymol.Qt`) |
| AI API | OpenAI-compatible API (SiliconFlow, OpenAI, etc.) |
| Async HTTP | `aiohttp>=3.8.0` |
| OpenAI SDK | `openai>=1.0.0` |
| i18n | Custom translation module (`i18n.py`)

## Project Structure

```
pymol-ai-assistant/
├── __init__.py           # Plugin entry point, dependency management
├── ai_chat_gui.py        # Main GUI module (~1200 lines)
│   ├── ChatMessageWidget    # Single chat message display
│   ├── LogPanel             # Log viewing panel
│   ├── ConfigDialog         # API configuration dialog
│   └── AIChatWindow         # Main chat window with streaming
├── pymol_tools.py        # PyMOL tool definitions (~1300 lines)
│   ├── get_tool_definitions()   # Returns OpenAI function schemas
│   └── execute_tool()           # Executes PyMOL operations
├── config_manager.py     # API configuration management (~200 lines)
│   ├── APIConfig            # Dataclass for API config
│   └── ConfigManager        # Singleton config manager
├── log_manager.py        # Logging system (~250 lines)
│   ├── LogEntry             # Dataclass for log entries
│   ├── LogManager           # Singleton log manager
│   └── LogType/LogLevel     # Enums for categorization
├── i18n.py               # Internationalization module (NEW)
│   ├── I18nManager          # Language management
│   └── TRANSLATIONS         # Translation dictionary
├── install.py            # Manual installation script
├── example_script.pml    # Example PyMOL script
├── example_setup.py      # Example Python script
├── README.md             # User documentation (Chinese)
└── QWEN.md               # AI memory file
```

## Architecture

### Plugin Initialization Flow

1. **Entry Point**: `__init__.py` → `__init_plugin__(app)` or `__init__(app)`
2. **Dependency Check**: `ensure_dependencies()` checks for `openai` and `aiohttp`
3. **GUI Initialization**: `ai_chat_gui.init_plugin(app)` registers menu item
4. **Lazy Loading**: Modules imported on-demand to avoid circular dependencies

### Module Dependencies

```
ai_chat_gui.py
    ├── config_manager.py  (get_config_manager, APIConfig)
    ├── log_manager.py     (get_log_manager, LogEntry, LogType, LogLevel)
    └── pymol_tools.py     (get_tool_definitions, execute_tool)

All modules:
    └── pymol (cmd, Qt, plugins)
```

### Key Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `AIChatWindow` | `ai_chat_gui.py` | Main window, streaming AI chat, tool execution |
| `ChatMessageWidget` | `ai_chat_gui.py` | Message bubble with styled text |
| `LogPanel` | `ai_chat_gui.py` | Log viewer with filtering |
| `ConfigDialog` | `ai_chat_gui.py` | API configuration UI |
| `ConfigManager` | `config_manager.py` | Persistent config storage |
| `LogManager` | `log_manager.py` | Session logging with callbacks |
| `I18nManager` | `i18n.py` | Language switching and translation |
| `APIConfig` | `config_manager.py` | Config dataclass |
| `LogEntry` | `log_manager.py` | Log entry dataclass |

## AI Tool System

Tools are defined in `pymol_tools.py` following OpenAI Function Calling schema.

### Tool Categories

1. **Structure Loading**: `pymol_fetch`, `pymol_load`
2. **Script Execution**: `pymol_run_script`, `pymol_run_pml`, `pymol_do_command`
3. **Information Query**: `pymol_get_info`, `pymol_get_selection_details`, `pymol_get_atom_info`, `pymol_get_residue_info`, `pymol_get_chain_info`, `pymol_get_object_info`, `pymol_get_distance`, `pymol_get_angle`, `pymol_get_dihedral`, `pymol_find_contacts`
4. **Display & Operation**: `pymol_show`, `pymol_hide`, `pymol_color`, `pymol_bg_color`, `pymol_zoom`, `pymol_rotate`, `pymol_select`, `pymol_label`, `pymol_reset`, `pymol_center`, `pymol_remove`, `pymol_set`
5. **Image Export**: `pymol_ray`, `pymol_png`

### Tool Execution Flow

1. AI decides to call tool(s) → streamed to client
2. `_on_tool_call()` displays tool call in chat
3. `execute_tool()` runs PyMOL command via `pymol.cmd`
4. `_on_tool_result()` displays result in chat
5. Tool result added to conversation history
6. AI receives result and continues (multi-turn tool calling supported)

## Configuration System

### Config File Location

- **Windows**: `%USERPROFILE%\.pymol_ai_assistant\config.json`
- **macOS/Linux**: `~/.pymol_ai_assistant/config.json`

### Config File Format

```json
{
  "configs": [...],
  "language": "zh"  // Language setting: "zh" (Chinese) or "en" (English)
}
```

### Default Configurations

```python
# SiliconFlow (Default)
api_url = "https://api.siliconflow.cn/v1"
model = "Pro/moonshotai/Kimi-K2.5"

# OpenAI
api_url = "https://api.openai.com/v1"
model = "gpt-4o"
```

### ConfigManager Features

- Multiple API configurations
- Mark one as default
- Import/export to JSON
- Persistent storage

## Logging System

### Log File Location

- **Windows**: `%USERPROFILE%\.pymol_ai_assistant\logs\session_YYYYMMDD_HHMMSS.jsonl`
- **macOS/Linux**: `~/.pymol_ai_assistant/logs/session_YYYYMMDD_HHMMSS.jsonl`

### Log Types

- `system` - System events
- `chat` - User/assistant messages
- `tool_call` - Tool invocations
- `tool_result` - Tool execution results
- `thinking` - AI reasoning (if supported by model)
- `response` - AI responses

### LogManager Features

- Real-time callbacks for UI updates
- Session-based file storage (JSON Lines format)
- Filtering by type and level
- Export to text file

## Code Style Guidelines

### Language

- **Comments**: Chinese (Simplified)
- **Docstrings**: Chinese
- **UI Text**: Chinese
- **Variable Names**: English, snake_case
- **Class Names**: English, PascalCase

### Type Hints

Use type hints throughout:

```python
def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    ...
```

### Error Handling

Use try-except with detailed logging:

```python
try:
    result = some_operation()
except Exception as e:
    tb = traceback.format_exc()
    print(f"[PyMOL AI Assistant] 错误: {e}")
    print(f"[PyMOL AI Assistant] Traceback:\n{tb}")
    return {"success": False, "message": str(e)}
```

### Singleton Pattern

Managers use module-level singleton instances:

```python
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
```

### Dataclasses for Data

```python
@dataclass
class APIConfig:
    name: str
    api_url: str
    api_key: str
    model: str
    is_default: bool = False
```

## Installation & Deployment

### No Build Process

This is a pure Python plugin with no build step required.

### Installation Methods

1. **Plugin Manager** (Recommended): Zip the folder, install via PyMOL Plugin Manager
2. **Manual**: Copy folder to PyMOL startup directory
3. **Script**: Run `install.py` from PyMOL command line

### Target Directories

- **Windows**: `%USERPROFILE%\AppData\Roaming\PyMOL\startup\`
- **macOS**: `~/Library/Preferences/PyMOL/startup/`
- **Linux**: `~/.pymol/startup/`

### Dependencies

Automatically installed on first load:
- `openai>=1.0.0`
- `aiohttp>=3.8.0`

## Testing

### No Formal Test Suite

This project does not use pytest, unittest, or any testing framework. Testing is done manually through:

1. Example scripts (`example_script.pml`, `example_setup.py`)
2. Interactive use in PyMOL
3. The `__main__` blocks in modules (minimal)

### Manual Testing Checklist

When making changes, test:
- [ ] Plugin loads without errors
- [ ] Dependencies install automatically
- [ ] API configuration dialog opens
- [ ] Chat sends/receives messages
- [ ] Tool calls execute correctly
- [ ] Streaming display works
- [ ] Logs are recorded and displayed
- [ ] Configuration persists across restarts

## Common Development Tasks

### Adding a New Tool

1. Add tool definition to `get_tool_definitions()` in `pymol_tools.py`:

```python
{
    "type": "function",
    "function": {
        "name": "pymol_new_tool",
        "description": "Tool description",
        "parameters": {...}
    }
}
```

2. Add implementation to `execute_tool()`:

```python
elif tool_name == "pymol_new_tool":
    param = arguments.get("param", "")
    cmd.some_pymol_command(param)
    return {"success": True, "message": "Done"}
```

3. Update system prompt in `ai_chat_gui.py` `_get_system_prompt()`

4. Update README.md documentation

5. Increment version in `__init__.py` and `README.md`

### Adding a New Config Field

1. Add field to `APIConfig` dataclass in `config_manager.py`
2. Update UI in `ConfigDialog` class in `ai_chat_gui.py`
3. Update `save_config()` and `on_config_selected()` methods

### Modifying UI

- Main window: `AIChatWindow` class in `ai_chat_gui.py`
- Message bubbles: `ChatMessageWidget` class
- Log panel: `LogPanel` class
- Config dialog: `ConfigDialog` class

## Security Considerations

1. **API Keys**: Stored in plain text in user's home directory
2. **Script Execution**: `pymol_run_script` can execute arbitrary Python code
3. **No Input Sanitization**: Tool arguments passed directly to PyMOL commands
4. **Local Only**: No network server exposed

## Version History

### v1.4.0
- Added bilingual support (Chinese/English) with language switch button
- Language preference is persisted across restarts
- All UI elements support dynamic language switching

### v1.2.0
- Added geometry tools (distance, angle, dihedral)
- Added contact finding
- Added detailed info tools (atom, residue, chain, object)
- Added by_b color scheme

### v1.1.0
- Added script execution support
- Added pymol_do_command, pymol_remove, pymol_set
- Improved color schemes

### v1.0.0
- Initial release

## Notes for AI Agents

1. **Chinese Language**: All user-facing text is in Chinese. Maintain this.
2. **PyMOL Context**: Code runs inside PyMOL's Python environment
3. **Qt Threading**: UI updates must use `QtCore.QMetaObject.invokeMethod` from background threads
4. **Streaming**: AI responses are streamed; handle partial content correctly
5. **Tool Loop**: AI can make multiple tool calls in sequence; conversation history must track this
