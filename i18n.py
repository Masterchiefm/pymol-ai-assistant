# -*- coding: utf-8 -*-
"""
国际化模块 - 支持中英文切换
"""

DEFAULT_LANGUAGE = "zh"

_current_language = DEFAULT_LANGUAGE

_language_change_callbacks = []

TRANSLATIONS = {
    "zh": {
        "window_title": "PyMOL AI 助手",
        "tab_chat": "对话",
        "tab_config": "配置",
        "tab_log": "日志",
        "input_placeholder": "请输入您的问题...",
        "send_button": "发送",
        "stop_button": "停止",
        "clear_chat": "清空",
        "thinking": "思考中...",
        "loading": "正在思考...",
        "using_tool": "使用工具",
        "tool_result": "工具结果",
        "tool_error": "工具错误",
        "user": "用户",
        "assistant": "AI助手",
        "config_title": "API 配置管理",
        "saved_configs": "已保存的配置：",
        "current_use": "[当前使用]",
        "name": "名称：",
        "provider": "提供商：",
        "api_url": "API URL：",
        "api_key": "API Key：",
        "model": "模型：",
        "api_version": "API 版本：",
        "api_base": "API Base：",
        "set_as_current": "设为当前使用配置",
        "new_button": "新建",
        "save_button": "保存",
        "delete_button": "删除",
        "import_button": "导入",
        "export_button": "导出",
        "close_button": "关闭",
        "test_connection": "测试连接",
        "language": "语言：",
        "chinese": "中文",
        "english": "English",
        "provider_openai": "OpenAI",
        "provider_azure": "Azure OpenAI",
        "provider_anthropic": "Anthropic (Claude)",
        "provider_gemini": "Google Gemini",
        "provider_deepseek": "DeepSeek",
        "provider_siliconflow": "SiliconFlow",
        "provider_moonshot": "Moonshot (Kimi)",
        "provider_zhipu": "智谱 AI",
        "provider_ollama": "Ollama (本地)",
        "provider_openrouter": "OpenRouter",
        "provider_together": "Together AI",
        "provider_custom": "自定义 (OpenAI 兼容)",
        "model_placeholder": "选择或输入模型名称",
        "api_url_placeholder": "可选，留空使用默认",
        "api_key_placeholder": "输入 API Key",
        "api_version_placeholder": "Azure API 版本",
        "confirm_delete": '确定要删除配置 "{}" 吗？',
        "confirm_clear_chat": "确定要清空所有对话记录吗？",
        "save_success": "保存成功！",
        "delete_success": "删除成功！",
        "test_success": "连接测试成功！",
        "test_failed": "连接测试失败：{}",
        "name_required": "请输入配置名称！",
        "model_required": "请输入模型名称！",
        "select_config_first": "请先选择一个配置！",
        "clear_log": "清空日志",
        "log_category": "日志类别：",
        "auto_scroll": "自动滚动",
        "error_no_config": "请先配置API信息！",
        "error_no_input": "请输入内容！",
        "error_api_request": "API请求错误：{}",
        "error_tool_execution": "工具执行错误：{}",
        "reasoning_model": "推理模型（支持思考过程）",
        "vision_model": "视觉模型（支持图片输入）",
        "normal_model": "普通模型",
        "menu_language": "语言",
        "menu_help": "帮助",
        "menu_about": "关于",
        "about_title": "关于 PyMOL AI Assistant",
        "about_version": "版本",
        "about_author": "作者",
        "about_email": "邮箱",
        "about_github": "GitHub",
        "about_donate": "打赏支持",
        "about_close": "关闭",
        "about_intro": "PyMOL AI Assistant 是一款基于人工智能的分子可视化辅助工具。\n\n它可以理解自然语言指令，自动控制PyMOL进行分子结构的可视化操作，包括加载结构、设置显示样式、测量距离等功能。\n\n现在使用 LiteLLM 驱动，支持 100+ LLM 提供商。",
        "donate_title": "打赏支持",
        "donate_hint": "请我喝杯奶茶吧",
        "donate_qr_missing": "二维码图片未找到\n请放置于 fig/donate.png",
        "advanced_settings": "高级设置",
        "show_advanced": "显示高级设置",
        "hide_advanced": "隐藏高级设置",
        "show_params": "查看参数",
        "hide_params": "收起参数",
        "show_result": "查看结果",
        "hide_result": "收起结果",
        "temperature": "温度：",
        "max_tokens": "最大词元数：",
        "timeout": "超时时间(秒)：",
        "import_image": "导入图片",
        "paste_image_hint": "或按 Ctrl+V 粘贴图片",
    },
    "en": {
        "window_title": "PyMOL AI Assistant",
        "tab_chat": "Chat",
        "tab_config": "Config",
        "tab_log": "Log",
        "input_placeholder": "Enter your question...",
        "send_button": "Send",
        "stop_button": "Stop",
        "clear_chat": "Clear",
        "thinking": "Thinking...",
        "loading": "Thinking...",
        "using_tool": "Using Tool",
        "tool_result": "Tool Result",
        "tool_error": "Tool Error",
        "user": "User",
        "assistant": "AI Assistant",
        "config_title": "API Configuration",
        "saved_configs": "Saved Configurations:",
        "current_use": "[Current]",
        "name": "Name:",
        "provider": "Provider:",
        "api_url": "API URL:",
        "api_key": "API Key:",
        "model": "Model:",
        "api_version": "API Version:",
        "api_base": "API Base:",
        "set_as_current": "Set as Current",
        "new_button": "New",
        "save_button": "Save",
        "delete_button": "Delete",
        "import_button": "Import",
        "export_button": "Export",
        "close_button": "Close",
        "test_connection": "Test Connection",
        "language": "Language:",
        "chinese": "Chinese",
        "english": "English",
        "provider_openai": "OpenAI",
        "provider_azure": "Azure OpenAI",
        "provider_anthropic": "Anthropic (Claude)",
        "provider_gemini": "Google Gemini",
        "provider_deepseek": "DeepSeek",
        "provider_siliconflow": "SiliconFlow",
        "provider_moonshot": "Moonshot (Kimi)",
        "provider_zhipu": "Zhipu AI",
        "provider_ollama": "Ollama (Local)",
        "provider_openrouter": "OpenRouter",
        "provider_together": "Together AI",
        "provider_custom": "Custom (OpenAI Compatible)",
        "model_placeholder": "Select or enter model name",
        "api_url_placeholder": "Optional, leave empty for default",
        "api_key_placeholder": "Enter API Key",
        "api_version_placeholder": "Azure API Version",
        "confirm_delete": 'Are you sure you want to delete config "{}"?',
        "confirm_clear_chat": "Are you sure you want to clear all chat history?",
        "save_success": "Saved successfully!",
        "delete_success": "Deleted successfully!",
        "test_success": "Connection test successful!",
        "test_failed": "Connection test failed: {}",
        "name_required": "Please enter a configuration name!",
        "model_required": "Please enter model name!",
        "select_config_first": "Please select a configuration first!",
        "clear_log": "Clear Log",
        "log_category": "Log Category:",
        "auto_scroll": "Auto Scroll",
        "error_no_config": "Please configure API settings first!",
        "error_no_input": "Please enter some text!",
        "error_api_request": "API request error: {}",
        "error_tool_execution": "Tool execution error: {}",
        "reasoning_model": "Reasoning Model (supports thinking)",
        "vision_model": "Vision Model (supports image input)",
        "normal_model": "Normal Model",
        "menu_language": "Language",
        "menu_help": "Help",
        "menu_about": "About",
        "about_title": "About PyMOL AI Assistant",
        "about_version": "Version",
        "about_author": "Author",
        "about_email": "Email",
        "about_github": "GitHub",
        "about_donate": "Donate",
        "about_close": "Close",
        "about_intro": "PyMOL AI Assistant is an AI-powered molecular visualization assistant.\n\nIt understands natural language commands and automatically controls PyMOL for molecular structure visualization, including loading structures, setting display styles, measuring distances, and more.\n\nNow powered by LiteLLM, supporting 100+ LLM providers.",
        "donate_title": "Donate",
        "donate_hint": "Buy me a bubble tea",
        "donate_qr_missing": "QR code image not found\nPlease place it at fig/donate.png",
        "advanced_settings": "Advanced Settings",
        "show_advanced": "Show Advanced Settings",
        "hide_advanced": "Hide Advanced Settings",
        "show_params": "Show Parameters",
        "hide_params": "Hide Parameters",
        "show_result": "Show Result",
        "hide_result": "Hide Result",
        "temperature": "Temperature:",
        "max_tokens": "Max Tokens:",
        "timeout": "Timeout (s):",
        "import_image": "Import Image",
        "paste_image_hint": "or press Ctrl+V to paste image",
    },
}


def set_language(lang):
    """设置语言"""
    global _current_language
    if lang in TRANSLATIONS and _current_language != lang:
        _current_language = lang
        for callback in _language_change_callbacks:
            try:
                callback(lang)
            except Exception:
                pass


def add_language_change_callback(callback):
    """添加语言变更回调函数"""
    if callback not in _language_change_callbacks:
        _language_change_callbacks.append(callback)


def remove_language_change_callback(callback):
    """移除语言变更回调函数"""
    if callback in _language_change_callbacks:
        _language_change_callbacks.remove(callback)


def get_language():
    """获取当前语言"""
    return _current_language


def _(key, *args):
    """获取翻译文本"""
    text = TRANSLATIONS.get(_current_language, TRANSLATIONS["zh"]).get(key, key)
    if args:
        try:
            text = text.format(*args)
        except:
            pass
    return text
