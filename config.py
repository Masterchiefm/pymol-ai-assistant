# -*- coding: utf-8 -*-
"""
配置管理模块 - 支持 LiteLLM 多提供商配置
"""

import os
import json
from . import i18n as _i18n

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".pymol_ai_assistant_config.json")

DEFAULT_CONFIG = {"current_config": None, "language": "zh", "configs": []}

PROVIDERS = {
    "siliconflow": {
        "name": "SiliconFlow",
        "api_base": "https://api.siliconflow.cn/v1",
        "models": [
            "Pro/moonshotai/Kimi-K2.5",
            "Pro/zai-org/GLM-5",
            "Pro/zai-org/GLM-5.1",
            "deepseek-ai/DeepSeek-V3.2",
            "deepseek-ai/DeepSeek-V3",
        ],
        "prefix": "openai/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
        "register_link": "https://cloud.siliconflow.cn/i/Su2ao83G",
    },
    "openai": {
        "name": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "models": ["gpt-4.1", "gpt-4o", "gpt-4o-mini", "o3", "o4-mini"],
        "prefix": "openai/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "api_base": "https://api.anthropic.com/v1",
        "models": [
            "claude-opus-4-6",
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
            "claude-sonnet-4-20250514",
            "claude-3-7-sonnet-20250219",
        ],
        "prefix": "anthropic/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "gemini": {
        "name": "Google Gemini",
        "api_base": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
        "prefix": "gemini/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "deepseek": {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com",
        "models": ["deepseek-v3.2", "deepseek-v3", "deepseek-r1", "deepseek-chat"],
        "prefix": "deepseek/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "dashscope": {
        "name": "通义千问 (DashScope)",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": [
            "qwen3-max",
            "qwen3-coder-plus",
            "qwen3-coder-flash",
            "qwen3.5-plus",
            "qwen-plus-latest",
            "qwq-plus",
        ],
        "prefix": "dashscope/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "minimax": {
        "name": "MiniMax",
        "api_base": "https://api.minimax.chat/v1",
        "models": [
            "MiniMax-M2.5",
            "MiniMax-M2.5-lightning",
            "MiniMax-M2.1",
            "MiniMax-M2.1-lightning",
        ],
        "prefix": "minimax/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "kimi_moonshot": {
        "name": "Kimi (Moonshot)",
        "api_base": "https://api.moonshot.cn/v1",
        "models": [
            "kimi-k2.5",
            "kimi-latest",
            "kimi-k2-thinking",
            "moonshot-v1-auto",
            "moonshot-v1-128k",
        ],
        "prefix": "moonshot/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "zai": {
        "name": "智谱 AI (ZAI \u56fd\u9645)",
        "api_base": "",
        "models": [
            "glm-5",
            "glm-5-code",
            "glm-4.7",
            "glm-4.6",
            "glm-4.5",
            "glm-4.5-flash",
        ],
        "prefix": "zai/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "zhipu": {
        "name": "智谱 AI (BigModel \u56fd\u5185)",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            "glm-5",
            "glm-5-code",
            "glm-4-plus",
            "glm-4-flash",
            "glm-4v-plus",
        ],
        "prefix": "openai/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "xai": {
        "name": "xAI (Grok)",
        "api_base": "https://api.x.ai/v1",
        "models": [
            "grok-4",
            "grok-4-latest",
            "grok-4-1-fast",
            "grok-3-latest",
            "grok-3-mini-fast-latest",
        ],
        "prefix": "xai/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "openrouter": {
        "name": "OpenRouter",
        "api_base": "https://openrouter.ai/api/v1",
        "models": [
            "openai/gpt-4.1",
            "openai/o3",
            "anthropic/claude-sonnet-4-5",
            "google/gemini-2.5-pro",
            "deepseek/deepseek-v3.2",
            "x-ai/grok-4",
        ],
        "prefix": "openrouter/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "ollama": {
        "name": "Ollama (\u672c\u5730)",
        "api_base": "http://localhost:11434/v1",
        "models": [
            "qwen3-coder",
            "deepseek-r1",
            "llama3.1",
            "qwen2.5",
            "mistral",
            "gemma3",
        ],
        "prefix": "ollama/",
        "requires_api_key": False,
        "requires_api_base": True,
        "requires_api_version": False,
    },
    "custom": {
        "name": "自定义 (OpenAI 兼容)",
        "api_base": "",
        "models": [],
        "prefix": "openai/",
        "requires_api_key": True,
        "requires_api_base": True,
        "requires_api_version": False,
    },
}


def get_provider_list():
    """获取提供商列表"""
    return list(PROVIDERS.keys())


def get_provider_info(provider_id):
    """获取提供商信息"""
    return PROVIDERS.get(provider_id, PROVIDERS["custom"])


def get_provider_models(provider_id):
    """获取提供商支持的模型列表"""
    provider = PROVIDERS.get(provider_id, PROVIDERS["custom"])
    return provider.get("models", [])


def get_litellm_model_name(provider_id, model_name):
    """
    获取 LiteLLM 格式的模型名称

    Args:
        provider_id: 提供商 ID
        model_name: 模型名称

    Returns:
        str: LiteLLM 格式的模型名称
    """
    provider = PROVIDERS.get(provider_id, PROVIDERS["custom"])
    prefix = provider.get("prefix", "openai/")

    if model_name.startswith(prefix):
        return model_name

    return f"{prefix}{model_name}"


def create_default_config(name, provider_id="siliconflow"):
    """
    创建默认配置

    Args:
        name: 配置名称
        provider_id: 提供商 ID

    Returns:
        dict: 默认配置
    """
    provider = get_provider_info(provider_id)
    models = provider.get("models", [])

    return {
        "name": name,
        "provider": provider_id,
        "api_url": provider.get("api_base", ""),
        "api_key": "",
        "model": models[0] if models else "",
        "api_version": "",
        "is_reasoning_model": False,
        "is_vision_model": False,
        "temperature": 0.7,
        "max_tokens": 8000,
        "timeout": 60,
    }


class ConfigManager:
    """配置管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._config = DEFAULT_CONFIG.copy()
        self.load()
        self._initialized = True

        lang = self._config.get("language", "zh")
        _i18n.set_language(lang)

    def load(self):
        """从文件加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
                    self._migrate_old_configs()
            except Exception as e:
                print("[PyMOL AI Assistant] 加载配置失败: {}".format(e))

    def _migrate_old_configs(self):
        """迁移旧配置格式"""
        configs = self._config.get("configs", [])
        for config in configs:
            if "provider" not in config:
                config["provider"] = self._detect_provider_from_url(
                    config.get("api_url", "")
                )
            if "api_version" not in config:
                config["api_version"] = ""
            if "temperature" not in config:
                config["temperature"] = 0.7
            if "max_tokens" not in config:
                config["max_tokens"] = 8000
            if "timeout" not in config:
                config["timeout"] = 60

    def _detect_provider_from_url(self, url):
        """从 URL 检测提供商"""
        url_lower = url.lower()
        if "openai.com" in url_lower:
            return "openai"
        elif "anthropic.com" in url_lower:
            return "anthropic"
        elif "generativelanguage.googleapis" in url_lower:
            return "gemini"
        elif "deepseek.com" in url_lower:
            return "deepseek"
        elif "siliconflow" in url_lower:
            return "siliconflow"
        elif "moonshot" in url_lower:
            return "kimi_moonshot"
        elif "bigmodel.cn" in url_lower:
            return "zhipu"
        elif "zai.chat" in url_lower or "z.ai" in url_lower:
            return "zai"
        elif "dashscope" in url_lower or "aliyuncs" in url_lower:
            return "dashscope"
        elif "minimax" in url_lower:
            return "minimax"
        elif "x.ai" in url_lower:
            return "xai"
        elif "localhost:11434" in url_lower or "127.0.0.1:11434" in url_lower:
            return "ollama"
        elif "openrouter.ai" in url_lower:
            return "openrouter"
        return "custom"

    def save(self):
        """保存配置到文件"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("[PyMOL AI Assistant] 保存配置失败: {}".format(e))
            return False

    def get_all_configs(self):
        """获取所有配置"""
        return self._config.get("configs", [])

    def get_config(self, name):
        """获取指定名称的配置"""
        for config in self._config.get("configs", []):
            if config.get("name") == name:
                return config
        return None

    def add_config(self, config):
        """添加配置"""
        existing = self.get_config(config.get("name"))
        if existing:
            existing.update(config)
        else:
            self._config["configs"].append(config)
        return self.save()

    def delete_config(self, name):
        """删除配置"""
        configs = self._config.get("configs", [])
        for i, config in enumerate(configs):
            if config.get("name") == name:
                del configs[i]
                if self._config.get("current_config") == name:
                    self._config["current_config"] = None
                return self.save()
        return False

    def set_current_config(self, name):
        """设置当前配置"""
        if name is None or self.get_config(name):
            self._config["current_config"] = name
            return self.save()
        return False

    def get_current_config(self):
        """获取当前配置"""
        name = self._config.get("current_config")
        if name:
            return self.get_config(name)
        return None

    def get_language(self):
        """获取语言设置"""
        return self._config.get("language", "zh")

    def set_language(self, lang):
        """设置语言"""
        self._config["language"] = lang
        _i18n.set_language(lang)
        return self.save()

    def get_tool_prompts(self):
        """获取自定义工具提示词"""
        return self._config.get("tool_prompts", {})

    def set_tool_prompts(self, prompts):
        """设置自定义工具提示词"""
        self._config["tool_prompts"] = prompts
        return self.save()

    def import_configs(self, filepath):
        """从文件导入配置"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                imported = json.load(f)
                if isinstance(imported, list):
                    for config in imported:
                        self.add_config(config)
                elif isinstance(imported, dict) and "configs" in imported:
                    for config in imported["configs"]:
                        self.add_config(config)
                return True
        except Exception as e:
            print("[PyMOL AI Assistant] 导入配置失败: {}".format(e))
            return False

    def export_configs(self, filepath):
        """导出配置到文件"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("[PyMOL AI Assistant] 导出配置失败: {}".format(e))
            return False


config_manager = ConfigManager()
