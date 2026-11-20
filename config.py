# -*- coding: utf-8 -*-
"""
配置管理模块 - 支持 LiteLLM 多提供商配置
"""

import os
import json
import base64 as _base64

_OBFUSCATION_PREFIX = "enc:"


def _obfuscate(value):
    if not value:
        return value
    return _OBFUSCATION_PREFIX + _base64.b64encode(value.encode("utf-8")).decode("ascii")


def _deobfuscate(value):
    if not value or not isinstance(value, str):
        return value
    if not value.startswith(_OBFUSCATION_PREFIX):
        return value
    try:
        return _base64.b64decode(value[len(_OBFUSCATION_PREFIX):].encode("ascii")).decode("utf-8")
    except Exception:
        return value

from . import i18n as _i18n

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".pymol_ai_assistant_config.json")

DEFAULT_CONFIG = {"current_config": None, "language": "zh", "configs": []}

# LiteLLM is a routing layer and does not impose one universal context limit.
# Keep authoritative provider limits here so the UI is not constrained by an
# out-of-date LiteLLM model-cost table.  Values are total context / max output.
DEFAULT_MAX_OUTPUT_TOKENS = 32768
CUSTOM_MAX_OUTPUT_TOKENS = 1000000

MODEL_LIMITS = {
    "gpt-5.6-sol": (1050000, 128000),
    "gpt-5.6-terra": (1050000, 128000),
    "gpt-5.6-luna": (1050000, 128000),
    "claude-fable-5": (1000000, 128000),
    "claude-opus-5": (1000000, 128000),
    "claude-sonnet-5": (1000000, 128000),
    "claude-haiku-4-5": (200000, 64000),
    "claude-haiku-4-5-20251001": (200000, 64000),
    "gemini-3.6-flash": (1000000, 64000),
    "gemini-3.5-flash": (1000000, 64000),
    "gemini-3.5-flash-lite": (1000000, 64000),
    "gemini-3.1-pro-preview": (1000000, 64000),
    "deepseek-flash": (1048576, 393216),
    "deepseek-v4-flash": (1048576, 393216),
    "deepseek-v4-pro": (1048576, 393216),
    "DeepSeek-V4-Flash": (1048576, 393216),
    "DeepSeek-V4-Pro": (1048576, 393216),
    "qwen3.7-max": (1000000, None),
    "qwen3.7-plus": (1000000, 64000),
    "qwen3.7-flash": (1000000, None),
    "qwen3.6-plus": (1000000, 64000),
    "qwen3.6-flash": (1000000, 64000),
    "qwen3-coder-plus": (1000000, None),
    "qwen3-coder-next": (262144, None),
    "qwen3.6-27b": (262144, None),
    "qwen3.5-397b-a17b": (262144, None),
    "MiniMax-M3": (1000000, None),
    "MiniMax-M2.7": (204800, None),
    "MiniMax-M2.7-highspeed": (204800, None),
    "glm-5.2": (1000000, 128000),
    "glm-5.1": (200000, 128000),
    "glm-5": (200000, 128000),
    "glm-5-turbo": (200000, 128000),
    "glm-5v-turbo": (200000, 128000),
    "glm-4.7": (200000, 128000),
    "grok-4.5": (500000, None),
    "kimi-k3": (1000000, None),
    "kimi-k2.7-code": (262144, None),
    "kimi-k2.7-code-highspeed": (262144, None),
    "kimi-k2.6": (262144, None),
}

PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com",
        "models": ["deepseek-flash", "deepseek-v4-pro"],
        "prefix": "deepseek/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
        "register_link": "https://platform.deepseek.com/api_keys",
        "usage_link": "https://platform.deepseek.com/usage",
    },
    "siliconflow": {
        "name": "SiliconFlow (硅基流动)",
        "api_base": "https://api.siliconflow.cn/v1",
        "models": [
            "zai-org/GLM-5.2",
            "Pro/zai-org/GLM-5.1",
            "moonshotai/Kimi-K2.7-Code",
            "Pro/moonshotai/Kimi-K2.6",
            "deepseek-ai/DeepSeek-V4-Pro",
            "deepseek-ai/DeepSeek-V4-Flash",
            "Qwen/Qwen3.6-35B-A3B",
            "Qwen/Qwen3.6-27B",
            "Qwen/Qwen3.5-397B-A17B",
            "Qwen/Qwen3-VL-32B-Instruct",
            "nex-agi/Nex-N2-Pro",
            "meituan-longcat/LongCat-2.0",
            "MiniMaxAI/MiniMax-M2.5",
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
        "models": ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"],
        "prefix": "openai/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "api_base": "https://api.anthropic.com/v1",
        "models": [
            "claude-fable-5",
            "claude-opus-5",
            "claude-sonnet-5",
            "claude-haiku-4-5",
        ],
        "prefix": "anthropic/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "gemini": {
        "name": "Google Gemini",
        "api_base": "https://generativelanguage.googleapis.com/v1beta",
        "models": [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-pro-preview",
        ],
        "prefix": "gemini/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "dashscope": {
        "name": "通义千问 (DashScope)",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": [
            "qwen3.7-max",
            "qwen3.7-plus",
            "qwen3.7-flash",
            "qwen3.6-plus",
            "qwen3.6-flash",
            "qwen3-coder-plus",
            "qwen3-coder-next",
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
            "MiniMax-M3",
            "MiniMax-M2.7",
            "MiniMax-M2.7-highspeed",
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
            "kimi-k3",
            "kimi-k2.7-code",
            "kimi-k2.7-code-highspeed",
            "kimi-k2.6",
        ],
        "prefix": "moonshot/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "zai": {
        "name": "ZAI (智谱-国际版)",
        "api_base": "https://api.z.ai/api/paas/v4",
        "models": [
            "glm-5.2",
            "glm-5.1",
            "glm-5",
            "glm-5-turbo",
            "glm-5v-turbo",
            "glm-4.7",
        ],
        "prefix": "zai/",
        "requires_api_key": True,
        "requires_api_base": False,
        "requires_api_version": False,
    },
    "zhipu": {
        "name": "BigModel (智谱-国内版)",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            "glm-5.2",
            "glm-5.1",
            "glm-5",
            "glm-5-turbo",
            "glm-5v-turbo",
            "glm-4.7",
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
            "grok-4.5",
            "grok-4",
            "grok-4-1-fast",
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
            "openai/gpt-5.6-sol",
            "anthropic/claude-sonnet-5",
            "google/gemini-3.6-flash",
            "deepseek/deepseek-v4-pro",
            "x-ai/grok-4.5",
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


def get_model_limits(model_name):
    """Return known provider limits without treating LiteLLM metadata as a cap."""
    if not model_name:
        return {
            "context_window": None,
            "max_output_tokens": CUSTOM_MAX_OUTPUT_TOKENS,
            "max_output_known": False,
        }

    bare_name = model_name.rsplit("/", 1)[-1]
    limits = MODEL_LIMITS.get(bare_name)
    if limits is None:
        bare_name_folded = bare_name.casefold()
        limits = next(
            (
                value
                for name, value in MODEL_LIMITS.items()
                if name.casefold() == bare_name_folded
            ),
            None,
        )
    if limits:
        return {
            "context_window": limits[0],
            "max_output_tokens": limits[1] or CUSTOM_MAX_OUTPUT_TOKENS,
            "max_output_known": limits[1] is not None,
        }

    return {
        "context_window": None,
        "max_output_tokens": CUSTOM_MAX_OUTPUT_TOKENS,
        "max_output_known": False,
    }


def create_default_config(name, provider_id="deepseek"):
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
        "max_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
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
                    for cfg in loaded.get("configs", []):
                        if "api_key" in cfg:
                            cfg["api_key"] = _deobfuscate(cfg["api_key"])
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
                config["max_tokens"] = DEFAULT_MAX_OUTPUT_TOKENS
            elif config["max_tokens"] == 8000:
                # 8000 was the old hard-coded UI default/near-maximum.
                config["max_tokens"] = DEFAULT_MAX_OUTPUT_TOKENS
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
            save_data = json.loads(json.dumps(self._config))
            for cfg in save_data.get("configs", []):
                if "api_key" in cfg and cfg["api_key"]:
                    cfg["api_key"] = _obfuscate(cfg["api_key"])
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
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

    def get_skills(self):
        """获取本地技能列表"""
        return self._config.get("skills", [])

    def set_skills(self, skills):
        """保存本地技能列表"""
        self._config["skills"] = skills
        return self.save()

    def import_configs(self, filepath):
        """从文件导入配置"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                imported = json.load(f)
                configs_list = []
                if isinstance(imported, list):
                    configs_list = imported
                elif isinstance(imported, dict) and "configs" in imported:
                    configs_list = imported["configs"]
                for cfg in configs_list:
                    if "api_key" in cfg:
                        cfg["api_key"] = _deobfuscate(cfg["api_key"])
                    self.add_config(cfg)
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
