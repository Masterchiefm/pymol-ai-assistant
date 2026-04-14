# PyMOL AI Assistant

## Project Overview

A PyMOL plugin that provides an AI chat interface for controlling PyMOL via natural language and tool calling. Distributed as a zip installed through PyMOL's Plugin Manager.

## Architecture

Flat single-package plugin — no build system, no `setup.py`, no `pyproject.toml`. The entire directory is zipped for release.

- `__init__.py` — Entry point. PyMOL calls `__init_plugin__(app)`. Auto-installs deps on first load.
- `main.py` — Qt GUI (dialog, chat, config, log tabs). Largest file (~2400 lines).
- `ai_client.py` — LiteLLM-based LLM client. Non-streaming with multi-turn tool calling loop.
- `tools.py` — Tool definitions (OpenAI function calling schema) and `ToolExecutor` that runs PyMOL commands.
- `config.py` — `ConfigManager` singleton, provider registry (12 providers). Config at `~/.pymol_ai_assistant_config.json`.
- `i18n.py` — zh/en translations. Default language is `zh`.
- `logger.py` — JSON-based logger. Logs at `~/.pymol_ai_assistant_log.json`.
- `markdown_renderer.py` — Renders AI responses as styled HTML (dark theme).
- `updater.py` — Background download thread for updates from Gitee/GitHub.
- `fig/` — Screenshots and donate QR code assets.

## Key Constraints

- **Cannot run standalone** — requires PyMOL runtime (`pymol.Qt`, `pymol.cmd`, `pymol.plugins`).
- **No tests, lint, typecheck, or CI** exist in this repo.
- Dependencies are auto-installed at import time from Tsinghua mirror (`pip install -i http://mirrors.tuna.tsinghua.edu.cn/...`). Required: `requests`, `PyQt5`, `litellm`, `json-repair`, `markdown`.
- `updater.py` imports `PyQt5` directly (not `pymol.Qt`), while all other GUI code uses `pymol.Qt`.

## Code Conventions

- Comments and UI strings are in Chinese. All user-facing text goes through `i18n._()` for bilingual support.
- Version is defined once in `__init__.py` as `__version__`.
- Global singletons: `ai_client.ai_client`, `config.config_manager`, `logger.logger`, `tools.tool_executor`.
- The `tool_executor` instance is created at module level in `tools.py` (imports `pymol.cmd` eagerly).
- Hardcoded local path exists in `main.py:2023` for PyMOL plugin installation — likely dev-only.

## Release / Distribution

Zip the entire repo directory as `pymol-ai-assistant.zip` and upload to GitHub/Gitee releases. Users install via PyMOL Plugin Manager. Update checker hits `gitee.com/api/v5/repos/MasterChiefm/pymol-ai-assistant/releases/latest`.
