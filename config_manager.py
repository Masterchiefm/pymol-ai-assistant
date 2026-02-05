"""
配置管理模块

管理 API 配置、记录和切换功能。
支持多配置文件保存和加载。
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# 配置文件目录
CONFIG_DIR = Path.home() / ".pymol_ai_assistant"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class APIConfig:
    """API 配置数据类"""
    name: str  # 配置名称（如 "SiliconFlow", "OpenAI"）
    api_url: str
    api_key: str
    model: str
    is_default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIConfig":
        return cls(**data)


class ConfigManager:
    """
    配置管理器
    
    负责：
    - 保存和加载 API 配置
    - 管理多个 API 配置
    - 设置默认配置
    """
    
    # 默认配置
    DEFAULT_CONFIGS = [
        APIConfig(
            name="SiliconFlow",
            api_url="https://api.siliconflow.cn/v1",
            api_key="",
            model="Pro/moonshotai/Kimi-K2.5",
            is_default=True
        ),
        APIConfig(
            name="OpenAI",
            api_url="https://api.openai.com/v1",
            api_key="",
            model="gpt-4o",
            is_default=False
        ),
    ]
    
    def __init__(self):
        self.configs: List[APIConfig] = []
        self._ensure_config_dir()
        self.load_configs()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    def load_configs(self):
        """从文件加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    configs_data = data.get("configs", [])
                    self.configs = [APIConfig.from_dict(c) for c in configs_data]
            except Exception as e:
                print(f"[ConfigManager] 加载配置失败: {e}")
                self.configs = []
        
        # 如果没有配置，使用默认配置
        if not self.configs:
            self.configs = [APIConfig(**asdict(c)) for c in self.DEFAULT_CONFIGS]
            self.save_configs()
    
    def save_configs(self):
        """保存配置到文件"""
        try:
            data = {
                "configs": [c.to_dict() for c in self.configs]
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败: {e}")
            return False
    
    def get_config(self, name: str) -> Optional[APIConfig]:
        """根据名称获取配置"""
        for config in self.configs:
            if config.name == name:
                return config
        return None
    
    def get_default_config(self) -> Optional[APIConfig]:
        """获取默认配置"""
        for config in self.configs:
            if config.is_default:
                return config
        # 如果没有默认配置，返回第一个
        return self.configs[0] if self.configs else None
    
    def add_config(self, config: APIConfig) -> bool:
        """添加新配置"""
        # 检查是否已存在同名配置
        existing = self.get_config(config.name)
        if existing:
            # 更新现有配置
            idx = self.configs.index(existing)
            self.configs[idx] = config
        else:
            self.configs.append(config)
        
        # 如果是第一个配置或设置为默认，更新默认标记
        if config.is_default:
            for c in self.configs:
                if c.name != config.name:
                    c.is_default = False
        
        return self.save_configs()
    
    def remove_config(self, name: str) -> bool:
        """删除配置"""
        config = self.get_config(name)
        if config:
            self.configs.remove(config)
            # 如果删除的是默认配置，设置新的默认
            if config.is_default and self.configs:
                self.configs[0].is_default = True
            return self.save_configs()
        return False
    
    def set_default(self, name: str) -> bool:
        """设置默认配置"""
        config = self.get_config(name)
        if config:
            for c in self.configs:
                c.is_default = (c.name == name)
            return self.save_configs()
        return False
    
    def get_all_configs(self) -> List[APIConfig]:
        """获取所有配置"""
        return self.configs.copy()
    
    def export_config(self, filepath: str) -> bool:
        """导出配置到 JSON 文件"""
        try:
            data = {
                "configs": [c.to_dict() for c in self.configs]
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ConfigManager] 导出配置失败: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """从 JSON 文件导入配置"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                configs_data = data.get("configs", [])
                
                for config_data in configs_data:
                    config = APIConfig.from_dict(config_data)
                    self.add_config(config)
            return True
        except Exception as e:
            print(f"[ConfigManager] 导入配置失败: {e}")
            return False


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
