# -*- coding: utf-8 -*-
'''
配置管理模块
'''

import os
import json
from . import i18n as _i18n

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.pymol_ai_assistant_config.json')

# 默认配置
DEFAULT_CONFIG = {
    'current_config': None,
    'language': 'zh',
    'configs': []
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

        # 加载配置后立即设置 i18n 模块的语言
        lang = self._config.get('language', 'zh')
        _i18n.set_language(lang)

    def load(self):
        """从文件加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
            except Exception as e:
                print("[PyMOL AI Assistant] 加载配置失败: {}".format(e))
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("[PyMOL AI Assistant] 保存配置失败: {}".format(e))
            return False
    
    def get_all_configs(self):
        """获取所有配置"""
        return self._config.get('configs', [])
    
    def get_config(self, name):
        """获取指定名称的配置"""
        for config in self._config.get('configs', []):
            if config.get('name') == name:
                return config
        return None
    
    def add_config(self, config):
        """添加配置"""
        # 检查是否已存在
        existing = self.get_config(config.get('name'))
        if existing:
            # 更新现有配置
            existing.update(config)
        else:
            self._config['configs'].append(config)
        return self.save()
    
    def delete_config(self, name):
        """删除配置"""
        configs = self._config.get('configs', [])
        for i, config in enumerate(configs):
            if config.get('name') == name:
                del configs[i]
                # 如果删除的是当前配置，清除当前配置
                if self._config.get('current_config') == name:
                    self._config['current_config'] = None
                return self.save()
        return False
    
    def set_current_config(self, name):
        """设置当前配置"""
        if name is None or self.get_config(name):
            self._config['current_config'] = name
            return self.save()
        return False
    
    def get_current_config(self):
        """获取当前配置"""
        name = self._config.get('current_config')
        if name:
            return self.get_config(name)
        return None
    
    def get_language(self):
        """获取语言设置"""
        return self._config.get('language', 'zh')
    
    def set_language(self, lang):
        """设置语言"""
        self._config['language'] = lang
        _i18n.set_language(lang)
        return self.save()
    
    def import_configs(self, filepath):
        """从文件导入配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported = json.load(f)
                if isinstance(imported, list):
                    for config in imported:
                        self.add_config(config)
                elif isinstance(imported, dict) and 'configs' in imported:
                    for config in imported['configs']:
                        self.add_config(config)
                return True
        except Exception as e:
            print("[PyMOL AI Assistant] 导入配置失败: {}".format(e))
            return False
    
    def export_configs(self, filepath):
        """导出配置到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("[PyMOL AI Assistant] 导出配置失败: {}".format(e))
            return False


# 全局配置管理器实例
config_manager = ConfigManager()
