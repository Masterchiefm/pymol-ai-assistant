"""
AI 聊天 GUI 模块

提供 PyQt5 界面，支持：
- 流式显示 AI 思考和输出（合并显示，颜色区分）
- 配置管理对话框
- 日志查看面板
- 工具调用显示和执行
"""

import sys
import json
import asyncio
import threading
import traceback
import copy
from typing import Optional, List, Dict, Any
from datetime import datetime

from pymol import cmd
from pymol.Qt import QtWidgets, QtCore, QtGui

# 导入其他模块
from .config_manager import get_config_manager, APIConfig
from .log_manager import get_log_manager, LogEntry, LogType, LogLevel
from .pymol_tools import get_tool_definitions, execute_tool
from .i18n import get_i18n_manager, t

Qt = QtCore.Qt


class ChatMessageWidget(QtWidgets.QFrame):
    """单个聊天消息显示部件"""
    
    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self.role = role
        self._current_text_widget: Optional[QtWidgets.QTextEdit] = None
        self._current_style = None
        self.i18n = get_i18n_manager()
        self.setup_ui()
    
    def setup_ui(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet(self.get_style())
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(2)
        
        # 头部（角色标签）
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.role == "user":
            role_text = self.i18n.t("role_user")
            role_color = "#569cd6"  # PyMOL 蓝色
        elif self.role == "assistant":
            role_text = self.i18n.t("role_assistant")
            role_color = "#4ec9b0"  # PyMOL 青色
        elif self.role == "tool":
            role_text = self.i18n.t("role_tool")
            role_color = "#dcdcaa"  # PyMOL 黄色
        else:
            role_text = ""
            role_color = "#808080"
        
        if role_text:
            self.role_label = QtWidgets.QLabel(f"<b style='color: {role_color};'>{role_text}</b>")
            self.role_label.setStyleSheet("font-size: 10px; margin: 0px; padding: 0px;")
            header_layout.addWidget(self.role_label)
            header_layout.addStretch()
            layout.addLayout(header_layout)
        
        # 内容区域
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setSpacing(0)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.content_layout)
    
    def get_style(self) -> str:
        """根据角色返回样式 - PyMOL 深色主题"""
        if self.role == "user":
            return """
                QFrame {
                    background-color: #2d3d4d;
                    border: 1px solid #3e5f7f;
                    border-radius: 8px;
                    margin: 2px 40px 2px 2px;
                }
            """
        elif self.role == "assistant":
            return """
                QFrame {
                    background-color: #2d3d3d;
                    border: 1px solid #3e7f6f;
                    border-radius: 8px;
                    margin: 2px 2px 2px 40px;
                }
            """
        elif self.role == "tool":
            return """
                QFrame {
                    background-color: #3d3d2d;
                    border: 1px solid #7f7f3e;
                    border-radius: 4px;
                    margin: 1px 15px 1px 15px;
                }
            """
        return ""
    
    def _get_or_create_text_widget(self, style: str) -> QtWidgets.QTextEdit:
        """获取或创建文本部件（按样式区分）"""
        # 如果样式变了，创建新的文本部件
        if self._current_text_widget is None or self._current_style != style:
            text_edit = QtWidgets.QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFrameStyle(QtWidgets.QFrame.NoFrame)
            text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # 设置背景透明和紧凑样式
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: transparent;
                    border: none;
                    font-size: 13px;
                    padding: 0px;
                    margin: 0px;
                }
            """)
            
            # 移除 viewport 的边距
            text_edit.viewport().setContentsMargins(0, 0, 0, 0)
            
            # 移除文档边距
            text_edit.document().setDocumentMargin(0)
            
            # 设置大小策略为 Preferred，确保高度自适应
            text_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            
            # 根据样式设置文本颜色 - PyMOL 深色主题
            if style == "thinking":
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: transparent;
                        border: none;
                        font-size: 12px;
                        color: #9cdcfe;
                        font-style: italic;
                        padding: 0px;
                        margin: 0px;
                    }
                """)
            elif style == "output":
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: transparent;
                        border: none;
                        font-size: 13px;
                        color: #d4d4d4;
                        padding: 0px;
                        margin: 0px;
                    }
                """)
            elif style == "tool_call":
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: transparent;
                        border: none;
                        font-size: 11px;
                        color: #dcdcaa;
                        font-family: Consolas, Monaco, monospace;
                        padding: 0px;
                        margin: 0px;
                    }
                """)
            elif style == "tool_result":
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: transparent;
                        border: none;
                        font-size: 11px;
                        color: #4ec9b0;
                        font-family: Consolas, Monaco, monospace;
                        padding: 0px;
                        margin: 0px;
                    }
                """)
            
            # 调整高度（紧凑，几乎无额外空间）
            text_edit.setMinimumHeight(1)
            text_edit.document().documentLayout().documentSizeChanged.connect(
                lambda size, te=text_edit: te.setFixedHeight(int(size.height()) + 2)
            )
            
            self.content_layout.addWidget(text_edit)
            self._current_text_widget = text_edit
            self._current_style = style
            
            # 添加前缀
            if style == "thinking":
                text_edit.setPlainText("💭 ")
            elif style == "tool_call":
                text_edit.setPlainText("⚙️ ")
            elif style == "tool_result":
                text_edit.setPlainText("✓ ")
        
        return self._current_text_widget
    
    def add_text(self, text: str, style: str = "normal"):
        """追加文本内容（流式）"""
        text_edit = self._get_or_create_text_widget(style)
        cursor = text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        text_edit.setTextCursor(cursor)
        text_edit.ensureCursorVisible()
    
    def add_html(self, html: str):
        """添加 HTML 内容"""
        text_edit = self._get_or_create_text_widget("normal")
        cursor = text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml(html)
        text_edit.setTextCursor(cursor)
        text_edit.ensureCursorVisible()


class HistoryPanel(QtWidgets.QWidget):
    """对话历史面板 - 显示 chat_history 的 JSON 内容"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = get_i18n_manager()
        self.setup_ui()
        
        # 注册语言变更回调
        self.i18n.add_callback(self._on_language_changed)
    
    def setup_ui(self):
        """设置界面"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # 工具栏
        toolbar = QtWidgets.QHBoxLayout()
        
        self.refresh_btn = QtWidgets.QPushButton("🔄 " + self.get_refresh_text())
        self.refresh_btn.clicked.connect(self.refresh_display)
        toolbar.addWidget(self.refresh_btn)
        
        toolbar.addStretch()
        
        self.copy_btn = QtWidgets.QPushButton("📋 " + self.get_copy_text())
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        toolbar.addWidget(self.copy_btn)
        
        layout.addLayout(toolbar)
        
        # 文本显示区域
        self.history_text = QtWidgets.QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
            }
        """)
        self.history_text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        layout.addWidget(self.history_text)
        
        # 状态标签
        self.status_label = QtWidgets.QLabel(self.get_empty_text())
        self.status_label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def get_refresh_text(self) -> str:
        return "刷新" if self.i18n.get_language_code() == "zh" else "Refresh"
    
    def get_copy_text(self) -> str:
        return "复制" if self.i18n.get_language_code() == "zh" else "Copy"
    
    def get_empty_text(self) -> str:
        return "暂无对话历史" if self.i18n.get_language_code() == "zh" else "No conversation history"
    
    def get_copied_text(self) -> str:
        return "已复制到剪贴板" if self.i18n.get_language_code() == "zh" else "Copied to clipboard"
    
    def update_history(self, chat_history: list):
        """更新历史显示"""
        if not chat_history:
            self.history_text.setPlainText("")
            self.status_label.setText(self.get_empty_text())
            return
        
        # 格式化显示 JSON
        try:
            json_str = json.dumps(chat_history, ensure_ascii=False, indent=2)
            self.history_text.setPlainText(json_str)
            msg_count = len(chat_history)
            self.status_label.setText(f"共 {msg_count} 条消息" if self.i18n.get_language_code() == "zh" else f"{msg_count} messages")
        except Exception as e:
            self.history_text.setPlainText(f"Error: {e}")
    
    def refresh_display(self):
        """刷新显示 - 由外部调用"""
        pass  # 实际刷新由 update_history 处理
    
    def copy_to_clipboard(self):
        """复制到剪贴板"""
        text = self.history_text.toPlainText()
        if text:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(text)
            self.status_label.setText(self.get_copied_text())
            QtCore.QTimer.singleShot(2000, lambda: self.update_status_label())
    
    def update_status_label(self):
        """恢复状态标签"""
        msg_count = self.history_text.toPlainText().count('"role"')
        if msg_count == 0:
            self.status_label.setText(self.get_empty_text())
        else:
            self.status_label.setText(f"共 {msg_count} 条消息" if self.i18n.get_language_code() == "zh" else f"{msg_count} messages")
    
    def _on_language_changed(self, language):
        """语言变更回调"""
        self.refresh_btn.setText("🔄 " + self.get_refresh_text())
        self.copy_btn.setText("📋 " + self.get_copy_text())
        self.update_status_label()
    
    def closeEvent(self, event):
        """关闭时取消回调注册"""
        self.i18n.remove_callback(self._on_language_changed)
        event.accept()


class LogPanel(QtWidgets.QWidget):
    """日志面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_manager = get_log_manager()
        self.i18n = get_i18n_manager()
        self.setup_ui()
        
        # 注册日志回调
        self.log_manager.add_callback(self.on_new_log)
        
        # 注册语言变更回调
        self.i18n.add_callback(self._on_language_changed)
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # 工具栏
        toolbar = QtWidgets.QHBoxLayout()
        
        self.filter_combo = QtWidgets.QComboBox()
        self._filter_keys = [
            "log_filter_all", "log_filter_system", "log_filter_api",
            "log_filter_chat", "log_filter_assistant", "log_filter_tool_call",
            "log_filter_tool_exec", "log_filter_tool_result", "log_filter_thinking", "log_filter_error"
        ]
        self.filter_combo.addItems([self.i18n.t(k) for k in self._filter_keys])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        self.filter_label = QtWidgets.QLabel(self.i18n.t("log_filter_label"))
        toolbar.addWidget(self.filter_label)
        toolbar.addWidget(self.filter_combo)
        
        toolbar.addStretch()
        
        self.clear_btn = QtWidgets.QPushButton(self.i18n.t("log_clear"))
        self.clear_btn.clicked.connect(self.clear_logs)
        toolbar.addWidget(self.clear_btn)
        
        self.export_btn = QtWidgets.QPushButton(self.i18n.t("log_export"))
        self.export_btn.clicked.connect(self.export_logs)
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # 日志显示区域
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 加载历史日志
        self.load_history()
    
    def load_history(self):
        """加载历史日志"""
        entries = self.log_manager.get_all_entries()
        for entry in entries:
            self.append_log_entry(entry)
    
    def on_new_log(self, entry: LogEntry):
        """新日志回调"""
        QtCore.QMetaObject.invokeMethod(
            self, "_append_log_safe",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(object, entry)
        )
    
    @QtCore.Slot(object)
    def _append_log_safe(self, entry: LogEntry):
        """线程安全地添加日志"""
        if self.should_show_entry(entry):
            self.append_log_entry(entry)
    
    def should_show_entry(self, entry: LogEntry) -> bool:
        """判断是否应该显示该日志条目"""
        filter_text = self.filter_combo.currentText()
        
        # 获取当前显示的过滤器索引
        filter_index = self.filter_combo.currentIndex()
        filter_key = self._filter_keys[filter_index] if 0 <= filter_index < len(self._filter_keys) else "log_filter_all"
        
        type_map_keys = [
            "log_filter_all", "log_filter_system", "log_filter_api",
            "log_filter_chat", "log_filter_assistant", "log_filter_tool_call",
            "log_filter_tool_exec", "log_filter_tool_result", "log_filter_thinking", "log_filter_error"
        ]
        type_map_values = [
            None, LogType.SYSTEM, LogType.API, LogType.CHAT_USER,
            LogType.CHAT_ASSISTANT, LogType.TOOL_CALL, LogType.TOOL_EXEC,
            LogType.TOOL_RESULT, LogType.THINKING, LogType.ERROR
        ]
        
        type_map = {self.i18n.t(k): v for k, v in zip(type_map_keys, type_map_values)}
        
        target_type = type_map.get(filter_text)
        if target_type is None:
            return True
        
        return entry.type == target_type.value
    
    def append_log_entry(self, entry: LogEntry):
        """添加日志条目到显示"""
        # 根据类型设置颜色
        color_map = {
            LogLevel.DEBUG.value: "#808080",
            LogLevel.INFO.value: "#d4d4d4",
            LogLevel.WARNING.value: "#ffcc00",
            LogLevel.ERROR.value: "#ff4444"
        }
        
        type_color_map = {
            LogType.API.value: "#c586c0",           # 紫色
            LogType.CHAT_USER.value: "#ce9178",     # 橙色
            LogType.CHAT_ASSISTANT.value: "#b5cea8", # 浅绿
            LogType.TOOL_CALL.value: "#4ec9b0",     # 青色
            LogType.TOOL_EXEC.value: "#dcdcaa",     # 黄色
            LogType.TOOL_RESULT.value: "#569cd6",   # 蓝色
            LogType.THINKING.value: "#9cdcfe",      # 浅蓝
            LogType.ERROR.value: "#f44747"          # 红色
        }
        
        color = type_color_map.get(entry.type, color_map.get(entry.level, "#d4d4d4"))
        
        dt = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
        html = f'<span style="color: #858585;">[{dt}]</span> '
        html += f'<span style="color: {color};">[{entry.type}] {entry.message}</span><br>'
        
        self.log_text.append(html)
    
    def apply_filter(self):
        """应用过滤器"""
        self.log_text.clear()
        self.load_history()
    
    def clear_logs(self):
        """清空日志"""
        self.log_manager.clear()
        self.log_text.clear()
    
    def export_logs(self):
        """导出日志"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.i18n.t("log_export_title"), "pymol_ai_logs.txt", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    for entry in self.log_manager.get_all_entries():
                        f.write(entry.format_display() + "\n")
                QtWidgets.QMessageBox.information(self, self.i18n.t("config_success_title"), self.i18n.t("log_export_success"))
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, self.i18n.t("config_error_title"), f"{self.i18n.t('log_export_fail')}: {e}")
    
    def _on_language_changed(self, language):
        """语言变更回调"""
        # 更新过滤器标签
        self.filter_label.setText(self.i18n.t("log_filter_label"))
        # 更新过滤器选项
        current_filter = self.filter_combo.currentText()
        self.filter_combo.clear()
        self.filter_combo.addItems([self.i18n.t(k) for k in self._filter_keys])
        # 尝试恢复之前的过滤器选择
        for i, key in enumerate(self._filter_keys):
            if self.i18n.t(key) == current_filter:
                self.filter_combo.setCurrentIndex(i)
                break
        # 更新按钮
        self.clear_btn.setText(self.i18n.t("log_clear"))
        self.export_btn.setText(self.i18n.t("log_export"))
    
    def closeEvent(self, event):
        """关闭时取消回调注册"""
        self.log_manager.remove_callback(self.on_new_log)
        self.i18n.remove_callback(self._on_language_changed)
        event.accept()


class ConfigDialog(QtWidgets.QDialog):
    """配置管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.i18n = get_i18n_manager()
        self.setup_ui()
        self.load_configs()
    
    def setup_ui(self):
        self.setWindowTitle(self.i18n.t("config_title"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # 深色主题样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                padding: 6px;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QCheckBox {
                color: #d4d4d4;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #5c5c5c;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:default {
                background-color: #0e639c;
                border: 1px solid #0e639c;
            }
            QPushButton:default:hover {
                background-color: #1177bb;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # 配置列表
        self.config_list = QtWidgets.QListWidget()
        self.config_list.currentItemChanged.connect(self.on_config_selected)
        self.config_list_label = QtWidgets.QLabel(self.i18n.t("config_list_label"))
        layout.addWidget(self.config_list_label)
        layout.addWidget(self.config_list)
        
        # 配置详情表单
        form_layout = QtWidgets.QFormLayout()
        
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText(self.i18n.t("config_name_placeholder"))
        self.form_name_label = self.i18n.t("config_name")
        form_layout.addRow(self.form_name_label, self.name_input)
        
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText(self.i18n.t("config_url_placeholder"))
        self.form_url_label = self.i18n.t("config_url")
        form_layout.addRow(self.form_url_label, self.url_input)
        
        self.key_input = QtWidgets.QLineEdit()
        self.key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.key_input.setPlaceholderText(self.i18n.t("config_key_placeholder"))
        self.form_key_label = self.i18n.t("config_key")
        form_layout.addRow(self.form_key_label, self.key_input)
        
        self.model_input = QtWidgets.QLineEdit()
        self.model_input.setPlaceholderText(self.i18n.t("config_model_placeholder"))
        self.form_model_label = self.i18n.t("config_model")
        form_layout.addRow(self.form_model_label, self.model_input)
        
        self.default_check = QtWidgets.QCheckBox(self.i18n.t("config_default"))
        form_layout.addRow(self.default_check)
        
        layout.addLayout(form_layout)
        
        # 按钮
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.new_btn = QtWidgets.QPushButton(self.i18n.t("config_btn_new"))
        self.new_btn.clicked.connect(self.new_config)
        btn_layout.addWidget(self.new_btn)
        
        self.save_btn = QtWidgets.QPushButton(self.i18n.t("config_btn_save"))
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = QtWidgets.QPushButton(self.i18n.t("config_btn_delete"))
        self.delete_btn.clicked.connect(self.delete_config)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        self.import_btn = QtWidgets.QPushButton(self.i18n.t("config_btn_import"))
        self.import_btn.clicked.connect(self.import_config)
        btn_layout.addWidget(self.import_btn)
        
        self.export_btn = QtWidgets.QPushButton(self.i18n.t("config_btn_export"))
        self.export_btn.clicked.connect(self.export_config)
        btn_layout.addWidget(self.export_btn)
        
        layout.addLayout(btn_layout)
        
        # 关闭按钮
        self.close_btn = QtWidgets.QPushButton(self.i18n.t("config_btn_close"))
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
    
    def load_configs(self):
        """加载配置列表"""
        self.config_list.clear()
        configs = self.config_manager.get_all_configs()
        for config in configs:
            display = f"{self.i18n.t('config_current') if config.is_default else ''}{config.name}"
            item = QtWidgets.QListWidgetItem(display)
            item.setData(Qt.UserRole, config)
            self.config_list.addItem(item)
    
    def on_config_selected(self, current, previous):
        """选择配置时的处理"""
        if current:
            config = current.data(Qt.UserRole)
            self.name_input.setText(config.name)
            self.url_input.setText(config.api_url)
            self.key_input.setText(config.api_key)
            self.model_input.setText(config.model)
            self.default_check.setChecked(config.is_default)
    
    def new_config(self):
        """新建配置"""
        self.name_input.clear()
        self.url_input.clear()
        self.key_input.clear()
        self.model_input.clear()
        self.default_check.setChecked(False)
        self.config_list.clearSelection()
    
    def save_config(self):
        """保存配置"""
        name = self.name_input.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, self.i18n.t("config_warning_title"), self.i18n.t("config_warning_name"))
            return
        
        config = APIConfig(
            name=name,
            api_url=self.url_input.text().strip(),
            api_key=self.key_input.text().strip(),
            model=self.model_input.text().strip(),
            is_default=self.default_check.isChecked()
        )
        
        if self.config_manager.add_config(config):
            QtWidgets.QMessageBox.information(self, self.i18n.t("config_success_title"), self.i18n.t("config_save_success"))
            self.load_configs()
        else:
            QtWidgets.QMessageBox.critical(self, self.i18n.t("config_error_title"), self.i18n.t("config_save_fail"))
    
    def delete_config(self):
        """删除配置"""
        current = self.config_list.currentItem()
        if not current:
            QtWidgets.QMessageBox.warning(self, self.i18n.t("config_warning_title"), self.i18n.t("config_warning_select"))
            return
        
        config = current.data(Qt.UserRole)
        reply = QtWidgets.QMessageBox.question(
            self, self.i18n.t("config_confirm_title"), self.i18n.t("config_confirm_delete", config.name)
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.config_manager.remove_config(config.name):
                QtWidgets.QMessageBox.information(self, self.i18n.t("config_success_title"), self.i18n.t("config_delete_success"))
                self.load_configs()
                self.new_config()
            else:
                QtWidgets.QMessageBox.critical(self, self.i18n.t("config_error_title"), self.i18n.t("config_delete_fail"))
    
    def import_config(self):
        """导入配置"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.i18n.t("config_import_title"), "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            if self.config_manager.import_config(filename):
                QtWidgets.QMessageBox.information(self, self.i18n.t("config_success_title"), self.i18n.t("config_import_success"))
                self.load_configs()
            else:
                QtWidgets.QMessageBox.critical(self, self.i18n.t("config_error_title"), self.i18n.t("config_import_fail"))
    
    def export_config(self):
        """导出配置"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "导出配置", "pymol_ai_config.json", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            if self.config_manager.export_config(filename):
                QtWidgets.QMessageBox.information(self, self.i18n.t("config_success_title"), self.i18n.t("config_export_success"))
            else:
                QtWidgets.QMessageBox.critical(self, self.i18n.t("config_error_title"), self.i18n.t("config_export_fail"))


class AIChatWindow(QtWidgets.QMainWindow):
    """
    AI 聊天主窗口
    
    提供流式 AI 对话界面，支持工具调用
    """
    
    def __init__(self):
        super().__init__()
        self.i18n = get_i18n_manager()
        self.setWindowTitle(self.i18n.t("app_title"))
        self.resize(500, 400)  # 设置初始大小
        
        self.config_manager = get_config_manager()
        self.log_manager = get_log_manager()
        
        # 加载保存的语言设置
        saved_lang = self.config_manager.get_language()
        self.i18n.set_language(saved_lang)
        
        self.current_config: Optional[APIConfig] = None
        self.chat_history: List[Dict[str, Any]] = []
        self.is_streaming = False
        self.current_message_widget: Optional[ChatMessageWidget] = None

        self.setup_ui()
        self.load_default_config()
        
        # 注册语言变更回调
        self.i18n.add_callback(self._on_language_changed)

    def setup_ui(self):
        """设置界面"""
        # 设置窗口背景色为深色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 8px 16px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 2px solid #0078d4;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3d3d3d;
            }
            QLabel {
                color: #d4d4d4;
                background-color: transparent;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #5c5c5c;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """)
        
        # 中央部件
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        # 主布局
        main_layout = QtWidgets.QVBoxLayout(central)

        # 主标签页
        main_tabs = QtWidgets.QTabWidget()

        # === 标签1: AI 对话 ===
        chat_tab = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_tab)

        # 工具栏
        toolbar = QtWidgets.QHBoxLayout()

        self.config_label = QtWidgets.QLabel(self.i18n.t("api_not_configured"))
        toolbar.addWidget(self.config_label)

        toolbar.addStretch()

        # 语言切换按钮
        self.lang_btn = QtWidgets.QPushButton(self.i18n.t("btn_language"))
        self.lang_btn.setToolTip("Switch Language / 切换语言")
        self.lang_btn.clicked.connect(self.toggle_language)
        toolbar.addWidget(self.lang_btn)

        self.config_btn = QtWidgets.QPushButton(self.i18n.t("btn_config"))
        self.config_btn.clicked.connect(self.open_config_dialog)
        toolbar.addWidget(self.config_btn)

        self.clear_btn = QtWidgets.QPushButton(self.i18n.t("btn_clear"))
        self.clear_btn.clicked.connect(self.clear_chat)
        toolbar.addWidget(self.clear_btn)

        chat_layout.addLayout(toolbar)

        # 聊天滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                min-height: 30px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6e6e6e;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
                border: none;
            }
        """)

        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(4)
        self.chat_layout.addStretch()

        scroll.setWidget(self.chat_container)
        chat_layout.addWidget(scroll)
        self.chat_scroll = scroll

        # 输入区域
        input_layout = QtWidgets.QHBoxLayout()

        self.input_text = QtWidgets.QTextEdit()
        self.input_text.setPlaceholderText(self.i18n.t("input_placeholder"))
        self.input_text.setMaximumHeight(80)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #3e3e3e;
                border-radius: 8px;
                padding: 8px;
                background-color: #2d2d2d;
                color: #d4d4d4;
            }
            QTextEdit::placeholder {
                color: #808080;
            }
        """)
        self.input_text.installEventFilter(self)
        input_layout.addWidget(self.input_text, stretch=1)

        self.send_btn = QtWidgets.QPushButton(self.i18n.t("btn_send"))
        self.send_btn.setMinimumHeight(60)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        # 停止按钮
        self.stop_btn = QtWidgets.QPushButton(self.i18n.t("btn_stop"))
        self.stop_btn.setMinimumHeight(60)
        self.stop_btn.setVisible(False)  # 初始隐藏
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #c75450;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d87470;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_streaming)
        input_layout.addWidget(self.stop_btn)

        chat_layout.addLayout(input_layout)

        self.chat_tab = chat_tab
        main_tabs.addTab(chat_tab, self.i18n.t("tab_chat"))

        # === 标签2: 日志 ===
        self.log_panel = LogPanel()
        self.main_tabs = main_tabs
        main_tabs.addTab(self.log_panel, self.i18n.t("tab_logs"))
        
        # === 标签3: 对话历史 ===
        self.history_panel = HistoryPanel()
        main_tabs.addTab(self.history_panel, self.i18n.t("tab_history"))

        main_layout.addWidget(main_tabs)
        
        # 菜单栏
        menubar = self.menuBar()
        self.help_menu = menubar.addMenu(self.i18n.t("menu_help"))
        
        self.about_action = QtWidgets.QAction(self.i18n.t("menu_about"), self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.help_menu.addAction(self.about_action)
        
        # 状态栏
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.i18n.t("status_ready"))
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理 Enter 键发送"""
        if obj == self.input_text and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def toggle_language(self):
        """切换语言"""
        new_lang = self.i18n.toggle_language()
        # 保存语言设置
        self.config_manager.set_language(self.i18n.get_language_code())
        self.log_manager.info(f"Language switched to: {new_lang.value}")
    
    def _update_history_panel(self):
        """更新历史面板（线程安全）"""
        QtCore.QMetaObject.invokeMethod(
            self, "_do_update_history_panel",
            QtCore.Qt.QueuedConnection
        )
    
    @QtCore.Slot()
    def _do_update_history_panel(self):
        """实际更新历史面板"""
        self.history_panel.update_history(self.chat_history)

    def _on_language_changed(self, language):
        """语言变更回调 - 更新所有 UI 文本"""
        # 更新窗口标题
        self.setWindowTitle(self.i18n.t("app_title"))
        
        # 更新语言切换按钮
        self.lang_btn.setText(self.i18n.t("btn_language"))
        
        # 更新工具栏按钮
        self.config_btn.setText(self.i18n.t("btn_config"))
        self.clear_btn.setText(self.i18n.t("btn_clear"))
        
        # 更新 API 标签
        if self.current_config:
            self.config_label.setText(f"API: {self.current_config.name}")
        else:
            self.config_label.setText(self.i18n.t("api_not_configured"))
        
        # 更新输入框占位符
        self.input_text.setPlaceholderText(self.i18n.t("input_placeholder"))
        
        # 更新发送/停止按钮
        if self.is_streaming:
            self.stop_btn.setText(self.i18n.t("btn_stop"))
        else:
            self.send_btn.setText(self.i18n.t("btn_send"))
        
        # 更新标签页标题
        self.main_tabs.setTabText(0, self.i18n.t("tab_chat"))
        self.main_tabs.setTabText(1, self.i18n.t("tab_logs"))
        self.main_tabs.setTabText(2, self.i18n.t("tab_history"))
        
        # 更新菜单
        self.help_menu.setTitle(self.i18n.t("menu_help"))
        self.about_action.setText(self.i18n.t("menu_about"))
        
        # 更新状态栏
        if not self.is_streaming:
            self.status_bar.showMessage(self.i18n.t("status_ready"))
    
    def load_default_config(self):
        """加载默认配置"""
        config = self.config_manager.get_default_config()
        if config:
            self.current_config = config
            self.config_label.setText(f"API: {config.name}")
            self.log_manager.info(self.i18n.t("log_loaded_config", config.name))
    
    def open_config_dialog(self):
        """打开配置对话框"""
        dialog = ConfigDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.load_default_config()
    
    def clear_chat(self):
        """清空聊天"""
        # 清除所有消息部件
        while self.chat_layout.count() > 1:  # 保留 stretch
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.chat_history.clear()
        self.current_message_widget = None
        self.log_manager.info(self.i18n.t("chat_cleared"))
        
        # 更新历史面板
        self.history_panel.update_history(self.chat_history)
    
    def add_message_widget(self, role: str) -> ChatMessageWidget:
        """添加新的消息部件"""
        widget = ChatMessageWidget(role)
        # 插入到 stretch 之前
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)
        
        # 滚动到底部
        QtCore.QTimer.singleShot(100, self.scroll_to_bottom)
        
        return widget
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """发送消息"""
        self.log_manager.debug("send_message 被调用", LogType.SYSTEM)

        if self.is_streaming:
            self.log_manager.debug("is_streaming=True，忽略发送请求", LogType.SYSTEM)
            return

        message = self.input_text.toPlainText().strip()
        if not message:
            self.log_manager.debug("消息为空，忽略", LogType.SYSTEM)
            return

        if not self.current_config:
            self.log_manager.error("未配置 API 配置", LogType.ERROR)
            QtWidgets.QMessageBox.warning(self, self.i18n.t("config_warning_title"), self.i18n.t("warn_api_not_configured"))
            return

        self.log_manager.info(f"用户: {message[:100]}...", LogType.CHAT_USER)

        # 清空输入
        self.input_text.clear()

        # 显示用户消息
        user_widget = self.add_message_widget("user")
        user_widget.add_text(message, "output")

        self.log_manager.chat_user(message)

        # 添加到历史
        self.chat_history.append({"role": "user", "content": message})
        self.log_manager.debug(f"当前对话历史长度: {len(self.chat_history)}", LogType.SYSTEM)
        
        # 更新历史面板
        self.history_panel.update_history(self.chat_history)

        # 开始流式响应
        self.start_streaming_response()
    
    def start_streaming_response(self):
        """开始流式响应"""
        self.is_streaming = True
        self.current_message_widget = None
        self.send_btn.setEnabled(False)
        self.send_btn.setText(self.i18n.t("btn_waiting"))
        self.send_btn.setVisible(False)  # 隐藏发送按钮
        self.stop_btn.setVisible(True)  # 显示停止按钮
        self.status_bar.showMessage(self.i18n.t("status_thinking"))

        # 创建新的 AI 消息部件
        self.current_message_widget = self.add_message_widget("assistant")

        # 在后台线程中运行 AI 请求
        self.ai_thread = threading.Thread(target=self._run_ai_stream)
        self.ai_thread.daemon = True
        self.ai_thread.start()
    
    def _run_ai_stream(self):
        """在后台线程中运行 AI 流式请求"""
        self.log_manager.debug("开始 AI 流式请求线程", LogType.SYSTEM)
        try:
            asyncio.run(self._stream_ai_response())
            self.log_manager.debug("AI 流式请求线程完成", LogType.SYSTEM)
        except Exception as e:
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            self.log_manager.error(f"AI 流式请求线程异常: {error_detail}", LogType.ERROR)
            self._on_stream_error(str(e))
    
    async def _stream_ai_response(self):
        """流式 AI 响应（支持多轮工具调用）"""
        self.log_manager.debug("开始流式 AI 响应", LogType.SYSTEM)

        try:
            from openai import AsyncOpenAI
            self.log_manager.debug("成功导入 openai.AsyncOpenAI", LogType.SYSTEM)
        except ImportError as e:
            self.log_manager.error(f"缺少 openai 包: {e}", LogType.ERROR)
            self._on_stream_error("缺少 openai 包，请安装: pip install openai")
            return

        config = self.current_config
        if not config:
            self.log_manager.error("未配置 API 配置", LogType.ERROR)
            self._on_stream_error("未配置 API")
            return

        self.log_manager.debug(f"使用配置: {config.name}, 模型: {config.model}", LogType.SYSTEM)

        try:
            client = AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.api_url
            )
            self.log_manager.debug("创建 AsyncOpenAI 客户端成功", LogType.SYSTEM)

            # 准备工具
            tools = get_tool_definitions()
            self.log_manager.debug(f"加载 {len(tools)} 个工具定义", LogType.SYSTEM)

            # 循环处理，直到 AI 不再调用工具
            max_iterations = 10  # 防止无限循环
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # 准备消息 - 使用深拷贝
                messages = []
                for i, msg in enumerate(self.chat_history):
                    # 使用深拷贝确保完全独立
                    new_msg = copy.deepcopy(msg)
                    
                    if new_msg.get("role") == "assistant":
                        # SiliconFlow API: 如果启用了 thinking 模式，所有 assistant 消息必须有 reasoning_content
                        if "reasoning_content" not in new_msg or new_msg.get("reasoning_content") is None:
                            new_msg["reasoning_content"] = ""
                        
                        # 如果没有 content 且有 tool_calls，需要添加空 content（SiliconFlow 要求）
                        if "content" not in new_msg and "tool_calls" in new_msg:
                            new_msg["content"] = ""
                    
                    messages.append(new_msg)
                
                # 添加系统提示
                system_prompt = self._get_system_prompt()
                messages.insert(0, {"role": "system", "content": system_prompt})
                
                # 简化日志：只显示发送的消息统计
                assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
                tool_count = sum(1 for m in messages if m.get("role") == "tool")
                self.log_manager.info(f"▶ 发送请求: {len(messages)} 条消息 (assistant={assistant_count}, tool={tool_count})", LogType.API)
                
                # 调试：打印最后一条 assistant 消息的详细内容（最新生成的）
                for m in reversed(messages):
                    if m.get("role") == "assistant" and m.get("tool_calls"):
                        has_rc = "reasoning_content" in m
                        rc_val = m.get("reasoning_content", "MISSING")
                        self.log_manager.debug(f"Assistant tool_call 消息: has_rc={has_rc}, rc='{rc_val[:50] if rc_val else '<empty>'}...', tools={len(m.get('tool_calls', []))}", LogType.API)
                        break
                response = await client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True
                )
                self.log_manager.debug("◀ 开始接收流式响应", LogType.API)

                # 处理流式响应
                full_content = ""
                full_reasoning = ""  # 捕获 AI 返回的 reasoning_content
                tool_calls_data = []

                async for chunk in response:
                    delta = chunk.choices[0].delta

                    # 处理内容
                    if delta.content:
                        content = delta.content
                        full_content += content
                        self._on_stream_content(content, is_thinking=False)

                    # 处理思考过程（如果模型支持）
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        reasoning = delta.reasoning_content
                        full_reasoning += reasoning
                        self._on_stream_content(reasoning, is_thinking=True)

                    # 处理工具调用
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            index = tc.index
                            
                            # 确保有足够的空间
                            while len(tool_calls_data) <= index:
                                tool_calls_data.append({"id": "", "name": "", "arguments": ""})

                            if tc.id:
                                tool_calls_data[index]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_data[index]["name"] = tc.function.name
                                    self.log_manager.info(f"🔧 工具调用: {tc.function.name}", LogType.TOOL_CALL)
                                if tc.function.arguments:
                                    tool_calls_data[index]["arguments"] += tc.function.arguments

                self.log_manager.info(f"◀ 响应完成: content={len(full_content)} 字符, reasoning={len(full_reasoning)} 字符, {len(tool_calls_data)} 个工具调用", LogType.API)

                # 处理工具调用
                tool_calls_for_history = []

                if not tool_calls_data:
                    # 没有工具调用，如果有内容则添加到历史并结束
                    if full_content:
                        self.chat_history.append({
                            "role": "assistant",
                            "content": full_content,
                            "reasoning_content": full_reasoning
                        })
                        self.log_manager.chat_assistant(full_content)
                    break

                self.log_manager.info(f"🔧 执行 {len(tool_calls_data)} 个工具调用", LogType.TOOL_EXEC)

                for tool_call in tool_calls_data:
                    if tool_call["name"] and tool_call["arguments"]:
                        tool_name = tool_call["name"]
                        args_str = tool_call["arguments"]

                        try:
                            args = json.loads(args_str)
                            # 显示工具调用（只显示一次）
                            self._on_tool_call(tool_name, args)
                            result = execute_tool(tool_name, args)
                            self._on_tool_result(tool_name, result)

                            # 保存工具调用信息到历史
                            tool_calls_for_history.append({
                                "id": tool_call["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": args_str
                                }
                            })

                            # 添加工具结果到历史
                            self.chat_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps(result, ensure_ascii=False)
                            })

                        except json.JSONDecodeError as e:
                            error_msg = f"参数解析失败: {e}"
                            self.log_manager.error(f"参数错误: {error_msg}", LogType.TOOL_EXEC)
                            error_result = {
                                "success": False,
                                "message": error_msg
                            }
                            self._on_tool_result(tool_name, error_result)
                            tool_calls_for_history.append({
                                "id": tool_call["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": args_str
                                }
                            })
                            self.chat_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
                            })
                        except Exception as e:
                            error_msg = f"执行出错: {e}"
                            self.log_manager.error(f"执行错误: {error_msg}", LogType.TOOL_EXEC)
                            error_result = {
                                "success": False,
                                "message": error_msg
                            }
                            self._on_tool_result(tool_name, error_result)

                            # 即使出错也要添加到历史
                            tool_calls_for_history.append({
                                "id": tool_call["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": args_str
                                }
                            })
                            self.chat_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps({"success": False, "message": str(e)}, ensure_ascii=False)
                            })

                # 添加 assistant 的工具调用消息到历史（如果有工具调用）
                if tool_calls_for_history:
                    # SiliconFlow API: thinking 模式下 assistant 消息必须有 reasoning_content
                    # 使用 AI 实际返回的 reasoning_content，如果没有则使用空字符串
                    assistant_msg = {
                        "role": "assistant",
                        "reasoning_content": full_reasoning if full_reasoning else "",
                        "tool_calls": tool_calls_for_history
                    }
                    # content: 有内容就加，没内容就不加（API 要求）
                    if full_content:
                        assistant_msg["content"] = full_content
                    self.chat_history.append(assistant_msg)

            self._on_stream_complete()
            self.log_manager.info("✓ 流式响应结束", LogType.API)

        except Exception as e:
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            self.log_manager.error(f"✗ 流式响应异常: {error_detail}", LogType.ERROR)
            self._on_stream_error(str(e))
    
    def _get_system_prompt(self) -> str:
        """获取系统提示"""
        return """你是一个 PyMOL 分子可视化助手。你可以使用工具来控制 PyMOL 软件。

结构加载与脚本执行：
- pymol_fetch: 从 PDB 数据库下载结构
- pymol_load: 加载本地文件
- pymol_run_script: 执行 Python 脚本（.py/.pym）
- pymol_run_pml: 执行 PyMOL 脚本（.pml）
- pymol_do_command: 执行 PyMOL 命令

信息查询（获取详细分子信息）：
- pymol_get_info: 获取基本信息（原子数、对象、链）
- pymol_get_selection_details: 获取选择集详细信息（残基列表、原子数、二级结构）- 用于回答"当前选中的是什么氨基酸"
- pymol_get_atom_info: 获取原子详细信息（坐标、B因子、元素等）
- pymol_get_residue_info: 获取残基详细信息
- pymol_get_chain_info: 获取链详细信息（残基范围、原子数）
- pymol_get_object_info: 获取对象详细信息
- pymol_get_distance: 计算两个选择之间的距离
- pymol_get_angle: 计算三个原子之间的角度
- pymol_get_dihedral: 计算四个原子之间的二面角
- pymol_find_contacts: 查找原子接触

显示与操作：
- pymol_show: 显示表示形式（lines, sticks, spheres, surface, mesh, ribbon, cartoon, labels, nonbonded）
- pymol_hide: 隐藏表示形式
- pymol_color: 设置颜色（red, green, blue, rainbow, by_element, by_chain, by_ss, by_resi, by_b 等）
- pymol_bg_color: 设置背景颜色
- pymol_zoom: 缩放视图
- pymol_rotate: 旋转视图
- pymol_select: 创建选择集
- pymol_label: 添加标签
- pymol_reset: 重置视图
- pymol_center: 居中视图
- pymol_remove: 删除对象或选择集
- pymol_set: 设置 PyMOL 参数

图像导出：
- pymol_ray: 光线追踪渲染
- pymol_png: 保存图像

计算距离时：
- 如果用户要求计算两个 selection 或两个对象之间的距离，且没有指定具体原子：
  - 如果是氨基酸：使用第一个氨基酸的 CA 原子或质心氨基酸的 CA 原子
  - 如果是核酸（DNA/RNA）：使用 P 原子（用于骨架分析）或 C1' 原子（用于碱基位置分析）

当用户询问关于当前选择的信息（如"选中的是什么氨基酸"），使用 pymol_get_selection_details 获取详细信息。
当用户请求涉及 PyMOL 操作时，请使用相应工具。使用工具后，向用户解释你做了什么。

重要：解释完操作后，不要给用户提建议或主动询问下一步，用户自己知道要做什么。
"""
    
    def _on_stream_content(self, content: str, is_thinking: bool = False):
        """流式内容回调（线程安全）"""
        QtCore.QMetaObject.invokeMethod(
            self, "_update_stream_content",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, content),
            QtCore.Q_ARG(bool, is_thinking)
        )
    
    @QtCore.Slot(str, bool)
    def _update_stream_content(self, content: str, is_thinking: bool):
        """更新流式内容"""
        if self.current_message_widget:
            style = "thinking" if is_thinking else "output"
            self.current_message_widget.add_text(content, style)
            self.scroll_to_bottom()
    
    def _on_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """工具调用回调"""
        QtCore.QMetaObject.invokeMethod(
            self, "_update_tool_call",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, tool_name),
            QtCore.Q_ARG(object, arguments)
        )
    
    @QtCore.Slot(str, object)
    def _update_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """更新工具调用显示"""
        # 在聊天中添加工具调用
        if self.current_message_widget:
            display_text = self.i18n.t("stream_calling", tool_name, json.dumps(arguments, ensure_ascii=False))
            self.current_message_widget.add_text(display_text, "tool_call")

        # 记录日志
        self.log_manager.tool_call(tool_name, arguments)

        self.scroll_to_bottom()
    
    def _on_tool_result(self, tool_name: str, result: Dict[str, Any]):
        """工具结果回调"""
        QtCore.QMetaObject.invokeMethod(
            self, "_update_tool_result",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, tool_name),
            QtCore.Q_ARG(object, result)
        )
    
    @QtCore.Slot(str, object)
    def _update_tool_result(self, tool_name: str, result: Dict[str, Any]):
        """更新工具结果显示"""
        success = result.get("success", False)
        message = result.get("message", "")

        # 在聊天中显示结果
        if self.current_message_widget:
            key = "stream_result_success" if success else "stream_result_fail"
            display_text = self.i18n.t(key, tool_name, message)
            self.current_message_widget.add_text(display_text, "tool_result")

        # 记录日志
        self.log_manager.tool_result(tool_name, result)

        self.scroll_to_bottom()
    
    def _on_stream_complete(self):
        """流完成回调（线程安全）"""
        QtCore.QMetaObject.invokeMethod(
            self, "_finish_stream",
            QtCore.Qt.QueuedConnection
        )

    def stop_streaming(self):
        """停止流式响应"""
        if self.is_streaming:
            self.log_manager.info("■ 用户停止流式响应", LogType.API)
            self.is_streaming = False
            # 重置 UI 状态
            self.send_btn.setEnabled(True)
            self.send_btn.setText("发送")
            self.send_btn.setVisible(True)
            self.stop_btn.setVisible(False)
            self.status_bar.showMessage("已停止")

    @QtCore.Slot()
    def _finish_stream(self):
        """完成流式响应"""
        self.is_streaming = False
        self.current_message_widget = None
        self.send_btn.setEnabled(True)
        self.send_btn.setText(self.i18n.t("btn_send"))
        self.send_btn.setVisible(True)  # 显示发送按钮
        self.stop_btn.setVisible(False)  # 隐藏停止按钮
        self.status_bar.showMessage(self.i18n.t("status_ready"))
        
        # 更新历史面板
        self.history_panel.update_history(self.chat_history)
    
    def _on_stream_error(self, error: str):
        """流错误回调（线程安全）"""
        QtCore.QMetaObject.invokeMethod(
            self, "_handle_stream_error",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, error)
        )
    
    @QtCore.Slot(str)
    def _handle_stream_error(self, error: str):
        """处理流式错误"""
        self.log_manager.error(f"✗ 流式错误: {error}", LogType.ERROR)
        self.is_streaming = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText(self.i18n.t("btn_send"))
        self.send_btn.setVisible(True)  # 显示发送按钮
        self.stop_btn.setVisible(False)  # 隐藏停止按钮
        self.status_bar.showMessage(self.i18n.t("error_stream", error))

        if self.current_message_widget:
            self.current_message_widget.add_text(f"错误: {error}", "tool_result")

        self.log_manager.error(f"AI 流式响应错误: {error}", LogType.ERROR)
        self.scroll_to_bottom()

    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()


# 全局窗口实例
_chat_window: Optional[AIChatWindow] = None


def init_plugin(app=None):
    """初始化插件"""
    global _chat_window
    
    from pymol import plugins
    
    def open_chat_window():
        global _chat_window
        if _chat_window is None:
            _chat_window = AIChatWindow()
        _chat_window.show()
        _chat_window.raise_()
        _chat_window.activateWindow()
    
    # 添加菜单项
    plugins.addmenuitemqt('AI Assistant', open_chat_window)
    
    # 记录日志
    get_log_manager().info("PyMOL AI Assistant 插件已加载")


def show_chat_window():
    """显示聊天窗口"""
    global _chat_window
    if _chat_window is None:
        _chat_window = AIChatWindow()
    _chat_window.show()
    _chat_window.raise_()


class AboutDialog(QtWidgets.QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = get_i18n_manager()
        self.setWindowTitle(self.i18n.t("about_title"))
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 深色主题样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
                background-color: transparent;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # 标题
        title_label = QtWidgets.QLabel("🤖 PyMOL AI Assistant")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4ec9b0;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本号
        from . import __version__
        version_label = QtWidgets.QLabel(f"Version {__version__}")
        version_label.setStyleSheet("font-size: 14px; color: #808080;")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        # 插件介绍
        intro_text = QtWidgets.QLabel(self.i18n.t("about_intro"))
        intro_text.setStyleSheet("font-size: 12px; color: #d4d4d4; line-height: 1.6;")
        intro_text.setAlignment(Qt.AlignLeft)
        intro_text.setWordWrap(True)
        layout.addWidget(intro_text)
        
        layout.addSpacing(20)
        
        # 作者信息
        info_widget = QtWidgets.QWidget()
        info_layout = QtWidgets.QFormLayout(info_widget)
        info_layout.setSpacing(8)
        info_layout.setLabelAlignment(Qt.AlignRight)
        
        author_label = QtWidgets.QLabel("Mo Qiqin")
        author_label.setStyleSheet("color: #d4d4d4;")
        info_layout.addRow(self.i18n.t("about_author"), author_label)
        
        email_label = QtWidgets.QLabel("moqiqin@live.com")
        email_label.setStyleSheet("color: #569cd6;")
        info_layout.addRow(self.i18n.t("about_email"), email_label)
        
        # GitHub 链接
        github_link = QtWidgets.QLabel(
            "<a href='https://github.com/Masterchiefm/pymol-ai-assistant' "
            "style='color: #569cd6; text-decoration: none;'>"
            "GitHub</a>"
        )
        github_link.setOpenExternalLinks(True)
        github_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        info_layout.addRow(self.i18n.t("about_github"), github_link)
        
        layout.addWidget(info_widget)
        layout.addStretch()
        
        # 捐赠按钮
        donate_btn = QtWidgets.QPushButton(self.i18n.t("about_donate"))
        donate_btn.setStyleSheet("""
            QPushButton {
                background-color: #d4a574;
                color: #1e1e1e;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e4b584;
            }
        """)
        donate_btn.clicked.connect(self.show_donate)
        layout.addWidget(donate_btn, alignment=Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton(self.i18n.t("about_close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
    
    def show_donate(self):
        """显示捐赠二维码"""
        donate_dialog = QtWidgets.QDialog(self)
        donate_dialog.setWindowTitle(self.i18n.t("about_donate"))
        donate_dialog.setFixedSize(350, 400)
        donate_dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
                background-color: transparent;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(donate_dialog)
        layout.setAlignment(Qt.AlignCenter)
        
        # 提示文字
        hint_label = QtWidgets.QLabel("如果本插件对您有帮助，欢迎打赏支持！")
        hint_label.setStyleSheet("color: #d4d4d4; font-size: 12px;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)
        
        layout.addSpacing(10)
        
        # 加载二维码图片
        import os
        qr_path = os.path.join(os.path.dirname(__file__), "fig", "donate.png")
        
        qr_label = QtWidgets.QLabel()
        if os.path.exists(qr_path):
            pixmap = QtGui.QPixmap(qr_path)
            # 缩放图片到合适大小
            scaled_pixmap = pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            qr_label.setPixmap(scaled_pixmap)
        else:
            qr_label.setText("二维码图片未找到\n请放置于 fig/donate.png")
            qr_label.setStyleSheet("color: #f44747; font-size: 12px;")
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)
        
        layout.addSpacing(10)
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """)
        close_btn.clicked.connect(donate_dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        donate_dialog.exec_()
