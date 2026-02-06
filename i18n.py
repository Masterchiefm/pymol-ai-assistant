"""
国际化 (i18n) 模块

管理多语言支持，默认中文，支持英文切换。
"""

from typing import Dict, Callable, List
from enum import Enum


class Language(Enum):
    """支持的语言"""
    CHINESE = "zh"
    ENGLISH = "en"


# 翻译字典
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ========== 通用 ==========
    "app_title": {
        "zh": "PyMOL AI Assistant",
        "en": "PyMOL AI Assistant"
    },
    "about_title": {
        "zh": "关于 PyMOL AI Assistant",
        "en": "About PyMOL AI Assistant"
    },
    
    # ========== 角色标签 ==========
    "role_user": {
        "zh": "👤 你",
        "en": "👤 You"
    },
    "role_assistant": {
        "zh": "🤖 AI",
        "en": "🤖 AI"
    },
    "role_tool": {
        "zh": "🔧 工具",
        "en": "🔧 Tool"
    },
    
    # ========== 按钮文本 ==========
    "btn_config": {
        "zh": "⚙️ 配置",
        "en": "⚙️ Config"
    },
    "btn_clear": {
        "zh": "🗑️ 清空",
        "en": "🗑️ Clear"
    },
    "btn_send": {
        "zh": "发送",
        "en": "Send"
    },
    "btn_stop": {
        "zh": "停止",
        "en": "Stop"
    },
    "btn_waiting": {
        "zh": "等待...",
        "en": "Waiting..."
    },
    "btn_language": {
        "zh": "🌐 English",
        "en": "🌐 中文"
    },
    
    # ========== 输入框提示 ==========
    "input_placeholder": {
        "zh": "输入消息... (Enter 发送, Shift+Enter 换行)",
        "en": "Type message... (Enter to send, Shift+Enter for new line)"
    },
    
    # ========== 状态栏 ==========
    "status_ready": {
        "zh": "就绪",
        "en": "Ready"
    },
    "status_thinking": {
        "zh": "AI 思考中...",
        "en": "AI thinking..."
    },
    "status_stopped": {
        "zh": "已停止",
        "en": "Stopped"
    },
    "api_not_configured": {
        "zh": "API: 未配置",
        "en": "API: Not Configured"
    },
    
    # ========== 标签页 ==========
    "tab_chat": {
        "zh": "💬 AI 对话",
        "en": "💬 Chat"
    },
    "tab_logs": {
        "zh": "📋 日志",
        "en": "📋 Logs"
    },
    "tab_history": {
        "zh": "📜 对话历史",
        "en": "📜 History"
    },
    
    # ========== 日志面板 ==========
    "log_filter_label": {
        "zh": "过滤:",
        "en": "Filter:"
    },
    "log_filter_all": {
        "zh": "全部",
        "en": "All"
    },
    "log_filter_system": {
        "zh": "系统",
        "en": "System"
    },
    "log_filter_api": {
        "zh": "API",
        "en": "API"
    },
    "log_filter_chat": {
        "zh": "对话",
        "en": "Chat"
    },
    "log_filter_assistant": {
        "zh": "AI回复",
        "en": "Assistant"
    },
    "log_filter_tool_call": {
        "zh": "工具调用",
        "en": "Tool Call"
    },
    "log_filter_tool_exec": {
        "zh": "工具执行",
        "en": "Tool Exec"
    },
    "log_filter_tool_result": {
        "zh": "工具结果",
        "en": "Tool Result"
    },
    "log_filter_thinking": {
        "zh": "思考",
        "en": "Thinking"
    },
    "log_filter_error": {
        "zh": "错误",
        "en": "Error"
    },
    "log_clear": {
        "zh": "清空",
        "en": "Clear"
    },
    "log_export": {
        "zh": "导出",
        "en": "Export"
    },
    "log_export_title": {
        "zh": "导出日志",
        "en": "Export Logs"
    },
    "log_export_success": {
        "zh": "日志已导出",
        "en": "Logs exported"
    },
    "log_export_fail": {
        "zh": "导出失败",
        "en": "Export failed"
    },
    
    # ========== 配置对话框 ==========
    "config_title": {
        "zh": "API 配置管理",
        "en": "API Configuration"
    },
    "config_list_label": {
        "zh": "已保存的配置:",
        "en": "Saved Configurations:"
    },
    "config_name": {
        "zh": "名称:",
        "en": "Name:"
    },
    "config_url": {
        "zh": "API URL:",
        "en": "API URL:"
    },
    "config_key": {
        "zh": "API Key:",
        "en": "API Key:"
    },
    "config_model": {
        "zh": "模型:",
        "en": "Model:"
    },
    "config_default": {
        "zh": "设为当前使用配置",
        "en": "Set as default"
    },
    "config_name_placeholder": {
        "zh": "配置名称（如 SiliconFlow）",
        "en": "Config name (e.g., SiliconFlow)"
    },
    "config_url_placeholder": {
        "zh": "https://api.example.com/v1",
        "en": "https://api.example.com/v1"
    },
    "config_key_placeholder": {
        "zh": "sk-...",
        "en": "sk-..."
    },
    "config_model_placeholder": {
        "zh": "模型名称（如 gpt-4o）",
        "en": "Model name (e.g., gpt-4o)"
    },
    "config_btn_new": {
        "zh": "新建",
        "en": "New"
    },
    "config_btn_save": {
        "zh": "保存",
        "en": "Save"
    },
    "config_btn_delete": {
        "zh": "删除",
        "en": "Delete"
    },
    "config_btn_import": {
        "zh": "导入",
        "en": "Import"
    },
    "config_btn_export": {
        "zh": "导出",
        "en": "Export"
    },
    "config_btn_close": {
        "zh": "关闭",
        "en": "Close"
    },
    "config_current": {
        "zh": "[当前使用] ",
        "en": "[Default] "
    },
    "config_save_success": {
        "zh": "配置已保存",
        "en": "Configuration saved"
    },
    "config_save_fail": {
        "zh": "保存配置失败",
        "en": "Failed to save configuration"
    },
    "config_delete_success": {
        "zh": "配置已删除",
        "en": "Configuration deleted"
    },
    "config_delete_fail": {
        "zh": "删除配置失败",
        "en": "Failed to delete configuration"
    },
    "config_import_title": {
        "zh": "导入配置",
        "en": "Import Configuration"
    },
    "config_import_success": {
        "zh": "配置已导入",
        "en": "Configuration imported"
    },
    "config_import_fail": {
        "zh": "导入配置失败",
        "en": "Failed to import configuration"
    },
    "config_export_title": {
        "zh": "导出配置",
        "en": "Export Configuration"
    },
    "config_export_success": {
        "zh": "配置已导出",
        "en": "Configuration exported"
    },
    "config_export_fail": {
        "zh": "导出配置失败",
        "en": "Failed to export configuration"
    },
    "config_warning_name": {
        "zh": "请输入配置名称",
        "en": "Please enter configuration name"
    },
    "config_warning_select": {
        "zh": "请先选择要删除的配置",
        "en": "Please select a configuration to delete"
    },
    "config_confirm_delete": {
        "zh": "确定要删除配置 '{}' 吗？",
        "en": "Are you sure you want to delete configuration '{}'?"
    },
    "config_confirm_title": {
        "zh": "确认",
        "en": "Confirm"
    },
    "config_warning_title": {
        "zh": "警告",
        "en": "Warning"
    },
    "config_error_title": {
        "zh": "错误",
        "en": "Error"
    },
    "config_success_title": {
        "zh": "成功",
        "en": "Success"
    },
    
    # ========== 关于对话框 ==========
    "about_intro": {
        "zh": "PyMOL AI Assistant 是一款基于 AI 工具技能（Function Calling）的 PyMOL 插件，\n让您可以使用自然语言控制 PyMOL 分子可视化软件。\n\n主要功能：\n• 🤖 AI 对话 - 使用自然语言控制 PyMOL\n• 🌊 流式显示 - 实时显示 AI 思考和输出\n• 🔧 工具调用 - AI 可直接操作 PyMOL（加载结构、设置样式、保存图像等）\n• ⚙️ 配置管理 - 支持多 API 配置（SiliconFlow、OpenAI 等）\n• 📋 日志系统 - 记录所有对话和工具调用",
        "en": "PyMOL AI Assistant is a PyMOL plugin based on AI Function Calling,\nallowing you to control PyMOL molecular visualization software using natural language.\n\nKey Features:\n• 🤖 AI Chat - Control PyMOL with natural language\n• 🌊 Streaming - Real-time AI thinking and output display\n• 🔧 Tool Calling - AI can directly operate PyMOL (load structures, set styles, save images, etc.)\n• ⚙️ Config Management - Support multiple API configurations (SiliconFlow, OpenAI, etc.)\n• 📋 Logging - Record all conversations and tool calls"
    },
    "about_author": {
        "zh": "作者:",
        "en": "Author:"
    },
    "about_email": {
        "zh": "邮箱:",
        "en": "Email:"
    },
    "about_github": {
        "zh": "项目主页:",
        "en": "Project:"
    },
    "about_donate": {
        "zh": "☕ 请我喝咖啡",
        "en": "☕ Buy me a coffee"
    },
    "about_close": {
        "zh": "关闭",
        "en": "Close"
    },
    
    # ========== 帮助菜单 ==========
    "menu_help": {
        "zh": "帮助",
        "en": "Help"
    },
    "menu_about": {
        "zh": "关于",
        "en": "About"
    },
    
    # ========== 警告和错误 ==========
    "warn_api_not_configured": {
        "zh": "请先配置 API",
        "en": "Please configure API first"
    },
    "error_stream": {
        "zh": "错误: {}",
        "en": "Error: {}"
    },
    "chat_cleared": {
        "zh": "聊天已清空",
        "en": "Chat cleared"
    },
    "log_loaded_config": {
        "zh": "加载当前使用配置: {}",
        "en": "Loaded default config: {}"
    },
    
    # ========== 流式响应状态 ==========
    "stream_calling": {
        "zh": "调用 {}({})",
        "en": "Calling {}({})"
    },
    "stream_result_success": {
        "zh": "✓ {}: {}",
        "en": "✓ {}: {}"
    },
    "stream_result_fail": {
        "zh": "✗ {}: {}",
        "en": "✗ {}: {}"
    },
}


class I18nManager:
    """
    国际化管理器
    
    负责：
    - 管理当前语言设置
    - 提供翻译功能
    - 通知语言变更
    """
    
    DEFAULT_LANGUAGE = Language.CHINESE
    
    def __init__(self):
        self._current_language = self.DEFAULT_LANGUAGE
        self._callbacks: List[Callable[[Language], None]] = []
    
    @property
    def current_language(self) -> Language:
        """获取当前语言"""
        return self._current_language
    
    def set_language(self, lang_code: str) -> None:
        """
        设置语言
        
        Args:
            lang_code: 语言代码 ('zh' 或 'en')
        """
        if lang_code == "en":
            new_lang = Language.ENGLISH
        else:
            new_lang = Language.CHINESE
        
        if new_lang != self._current_language:
            self._current_language = new_lang
            self._notify_change()
    
    def toggle_language(self) -> Language:
        """切换语言"""
        if self._current_language == Language.CHINESE:
            self._current_language = Language.ENGLISH
        else:
            self._current_language = Language.CHINESE
        self._notify_change()
        return self._current_language
    
    def get_text(self, key: str) -> str:
        """
        获取翻译文本
        
        Args:
            key: 翻译键名
            
        Returns:
            翻译后的文本
        """
        if key in TRANSLATIONS:
            return TRANSLATIONS[key].get(self._current_language.value, key)
        return key
    
    def t(self, key: str, *args) -> str:
        """
        获取翻译文本（支持格式化）
        
        Args:
            key: 翻译键名
            *args: 格式化参数
            
        Returns:
            格式化后的翻译文本
        """
        text = self.get_text(key)
        if args:
            return text.format(*args)
        return text
    
    def get_language_code(self) -> str:
        """获取当前语言代码"""
        return self._current_language.value
    
    def add_callback(self, callback: Callable[[Language], None]) -> None:
        """添加语言变更回调"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Language], None]) -> None:
        """移除语言变更回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_change(self) -> None:
        """通知所有回调语言已变更"""
        for callback in self._callbacks:
            callback(self._current_language)


# 全局实例
_i18n_manager: I18nManager = None


def get_i18n_manager() -> I18nManager:
    """获取全局国际化管理器实例"""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager


def t(key: str, *args) -> str:
    """快捷翻译函数"""
    return get_i18n_manager().t(key, *args)
