# -*- coding: utf-8 -*-
'''
主模块 - 包含AI助手对话框主界面（深色主题）
'''

import os
import json
from datetime import datetime

from pymol.Qt import QtCore, QtWidgets, QtGui

from . import i18n, config, logger, ai_client, tools


# 版本号
__version__ = '2.0.0'


# 颜色定义 - 深色主题
COLORS = {
    'bg_dark': '#2D2D2D',
    'bg_darker': '#1E1E1E',
    'bg_panel': '#404040',
    'bg_input': '#4A4A4A',
    'bg_message_user': '#2A3F2A',
    'bg_message_ai': '#2A3A4A',
    'bg_message_think': '#3A3A2A',
    'bg_message_tool': '#2A2A3A',
    'text_primary': '#FFFFFF',
    'text_secondary': '#CCCCCC',
    'text_muted': '#888888',
    'accent_blue': '#5DADE2',
    'accent_green': '#58D68D',
    'accent_yellow': '#F5B041',
    'accent_purple': '#AF7AC5',
    'accent_cyan': '#5DDBE2',
    'accent_red': '#E74C3C',
    'border': '#555555',
}


class StyledButton(QtWidgets.QPushButton):
    """自定义样式按钮"""
    
    def __init__(self, text, parent=None, accent=False, danger=False):
        super().__init__(text, parent)
        self.accent = accent
        self.danger = danger
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.update_style()
    
    def update_style(self):
        if self.danger:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 20px;
                    padding: 10px 30px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
                QPushButton:pressed {
                    background-color: #A93226;
                }
                QPushButton:disabled {
                    background-color: #555555;
                    color: #888888;
                }
            """)
        elif self.accent:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #5DADE2;
                    color: #2D2D2D;
                    border: none;
                    border-radius: 20px;
                    padding: 10px 30px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #76C5F0;
                }
                QPushButton:pressed {
                    background-color: #4A9BC4;
                }
                QPushButton:disabled {
                    background-color: #555555;
                    color: #888888;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    border-radius: 15px;
                    padding: 8px 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #2D2D2D;
                }
            """)


class MessageWidget(QtWidgets.QFrame):
    """单条消息组件"""
    
    def __init__(self, role, content, parent=None):
        super().__init__(parent)
        self.role = role
        self.raw_content = content
        self.setObjectName("messageWidget")
        self.setup_ui()
        self.set_content(content)
    
    def setup_ui(self):
        # 去掉边框
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setLineWidth(0)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # 角色标签
        role_text = {
            'user': 'User',
            'assistant': 'AI',
            'thinking': i18n._('thinking'),
            'tool': i18n._('using_tool'),
            'tool_result': i18n._('tool_result'),
            'tool_error': i18n._('tool_error'),
        }.get(self.role, self.role)
        
        self.role_label = QtWidgets.QLabel("<b>%s:</b>" % role_text)
        
        if self.role == 'user':
            role_color = COLORS['accent_green']
            self.bg_color = COLORS['bg_message_user']
        elif self.role == 'assistant':
            role_color = COLORS['accent_blue']
            self.bg_color = COLORS['bg_message_ai']
        elif self.role == 'thinking':
            role_color = COLORS['accent_yellow']
            self.bg_color = COLORS['bg_message_think']
        elif self.role in ['tool', 'tool_result', 'tool_error']:
            role_color = COLORS['accent_purple']
            self.bg_color = COLORS['bg_message_tool']
        else:
            role_color = COLORS['text_primary']
            self.bg_color = COLORS['bg_panel']
        
        self.role_label.setStyleSheet("color: %s; font-size: 14px; background: transparent;" % role_color)
        layout.addWidget(self.role_label)
        
        # 内容标签 - 设置为可复制
        self.content_label = QtWidgets.QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setTextFormat(QtCore.Qt.RichText)
        self.content_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
        self.content_label.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.content_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                line-height: 1.6;
                background: transparent;
            }
        """)
        layout.addWidget(self.content_label)
        
        # 设置背景 - 使用palette而不是stylesheet
        self.setStyleSheet("""
            #messageWidget {
                background-color: %s;
                border: none;
                border-radius: 12px;
            }
        """ % self.bg_color)
    
    def set_content(self, content):
        """设置内容，支持不同颜色的文本"""
        self.raw_content = content
        
        # 转义HTML
        escaped = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # 处理不同样式的文本
        lines = escaped.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith('使用工具:') or line.strip().startswith('Using tool:'):
                formatted_lines.append('<span style="color: #58D68D;">%s</span>' % line)
            elif line.strip().startswith('思考:') or line.strip().startswith('Thinking:'):
                formatted_lines.append('<span style="color: #F5B041;">%s</span>' % line)
            elif any(kw in line for kw in ['成功', '完成', 'success']):
                formatted_lines.append('<span style="color: #5DDBE2;">%s</span>' % line)
            elif line.strip().startswith('错误:') or line.strip().startswith('Error:'):
                formatted_lines.append('<span style="color: #F07178;">%s</span>' % line)
            else:
                formatted_lines.append(line)
        
        html_content = '<br>'.join(formatted_lines)
        self.content_label.setText(html_content)
    
    def append_content(self, text):
        """追加内容"""
        self.set_content(self.raw_content + text)


class ChatWidget(QtWidgets.QWidget):
    """聊天标签页"""
    
    message_sent = QtCore.Signal(str)
    stop_requested = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self.current_message_widget = None
        self.is_thinking = False
        self.is_streaming = False
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 消息显示区域（带圆角面板）- 使用bg_panel颜色，无边框
        self.chat_panel = QtWidgets.QFrame()
        self.chat_panel.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border-radius: 15px;
                border: none;
            }
        """)
        
        chat_layout = QtWidgets.QVBoxLayout(self.chat_panel)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(8)
        
        # 清除按钮
        clear_layout = QtWidgets.QHBoxLayout()
        clear_layout.addStretch()
        
        self.clear_btn = StyledButton(i18n._('clear_chat'))
        self.clear_btn.setFixedSize(85, 30)
        self.clear_btn.clicked.connect(self.clear_chat)
        clear_layout.addWidget(self.clear_btn)
        
        chat_layout.addLayout(clear_layout)
        
        # 消息滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2D2D2D;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #888888;
            }
        """)
        
        # 消息容器 - 使用透明背景
        self.messages_container = QtWidgets.QWidget()
        self.messages_container.setStyleSheet("background: transparent;")
        self.messages_layout = QtWidgets.QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(10)
        self.messages_layout.setContentsMargins(5, 5, 5, 5)
        self.messages_layout.addStretch()
        
        scroll.setWidget(self.messages_container)
        chat_layout.addWidget(scroll)
        
        layout.addWidget(self.chat_panel, stretch=1)
        
        # 输入区域面板
        self.input_panel = QtWidgets.QFrame()
        self.input_panel.setStyleSheet("""
            QFrame {
                background-color: #4A4A4A;
                border-radius: 15px;
                border: none;
            }
        """)
        
        input_layout = QtWidgets.QVBoxLayout(self.input_panel)
        input_layout.setContentsMargins(15, 12, 15, 12)
        input_layout.setSpacing(8)
        
        # 输入框
        self.input_text = QtWidgets.QTextEdit()
        self.input_text.setPlaceholderText(i18n._('input_placeholder'))
        self.input_text.setMaximumHeight(80)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                font-size: 14px;
                line-height: 1.5;
            }
            QTextEdit::placeholder {
                color: #888888;
            }
        """)
        input_layout.addWidget(self.input_text)
        
        # 发送按钮（右下角）
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        
        self.send_btn = StyledButton(i18n._('send_button'), accent=True)
        self.send_btn.setFixedSize(100, 40)
        self.send_btn.clicked.connect(self.on_send_clicked)
        btn_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(btn_layout)
        
        layout.addWidget(self.input_panel)
        
        # 事件过滤器
        self.input_text.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if obj == self.input_text and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and not event.modifiers() & QtCore.Qt.ShiftModifier:
                self.on_send_clicked()
                return True
        return super().eventFilter(obj, event)
    
    def on_send_clicked(self):
        """发送按钮点击"""
        if self.is_streaming:
            self.stop_requested.emit()
            return
        
        text = self.input_text.toPlainText().strip()
        if text:
            self.add_message('user', text)
            self.input_text.clear()
            self.message_sent.emit(text)
            self.set_streaming_state(True)
    
    def set_streaming_state(self, streaming):
        """设置流式状态"""
        self.is_streaming = streaming
        if streaming:
            self.send_btn.setText(i18n._('stop_button'))
            self.send_btn.accent = False
            self.send_btn.danger = True
            self.send_btn.update_style()
        else:
            self.send_btn.setText(i18n._('send_button'))
            self.send_btn.accent = True
            self.send_btn.danger = False
            self.send_btn.update_style()
    
    def add_message(self, role, content):
        """添加消息"""
        msg_widget = MessageWidget(role, content)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, msg_widget)
        self.messages.append({'role': role, 'widget': msg_widget})
        self.current_message_widget = msg_widget
        self.scroll_to_bottom()
        return msg_widget
    
    def start_message(self, role):
        """开始一条新消息"""
        self.current_message_widget = self.add_message(role, '')
        return self.current_message_widget
    
    def append_to_current(self, text):
        """追加到当前消息"""
        if self.current_message_widget:
            self.current_message_widget.append_content(text)
            self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        QtCore.QTimer.singleShot(50, self._do_scroll)
    
    def _do_scroll(self):
        if self.messages_container.parent():
            scroll = self.messages_container.parent().parent()
            if isinstance(scroll, QtWidgets.QScrollArea):
                scrollbar = scroll.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """清空对话"""
        reply = QtWidgets.QMessageBox.question(
            self,
            i18n._('clear_chat'),
            i18n._('confirm_clear_chat'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            for msg in self.messages:
                msg['widget'].deleteLater()
            self.messages.clear()
            self.current_message_widget = None
    
    def get_messages_for_api(self):
        """获取API用的消息历史"""
        api_messages = []
        for msg in self.messages:
            role = msg['role']
            if role in ['user', 'assistant']:
                api_messages.append({
                    'role': role,
                    'content': msg['widget'].raw_content
                })
        return api_messages


class ConfigWidget(QtWidgets.QWidget):
    """配置标签页"""

    config_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config_name = None
        self.labels = {}  # 保存需要更新文本的标签引用
        self.setup_ui()
        self.load_configs()

    def update_language(self):
        """更新界面语言"""
        # 更新标签页标题（由主窗口调用 setTabText）
        # 更新保存的配置列表标签
        if hasattr(self, 'labels') and 'list_label' in self.labels:
            self.labels['list_label'].setText(i18n._('saved_configs'))

        # 更新表单标签
        if hasattr(self, 'labels'):
            if 'name_label' in self.labels:
                self.labels['name_label'].setText(i18n._('name'))
            if 'url_label' in self.labels:
                self.labels['url_label'].setText(i18n._('api_url'))
            if 'key_label' in self.labels:
                self.labels['key_label'].setText(i18n._('api_key'))
            if 'model_label' in self.labels:
                self.labels['model_label'].setText(i18n._('model'))

        # 更新复选框
        if hasattr(self, 'reasoning_checkbox'):
            self.reasoning_checkbox.setText(i18n._('reasoning_model'))
        if hasattr(self, 'current_checkbox'):
            self.current_checkbox.setText(i18n._('set_as_current'))

        # 更新按钮
        if hasattr(self, 'new_btn'):
            self.new_btn.setText(i18n._('new_button'))
        if hasattr(self, 'save_btn'):
            self.save_btn.setText(i18n._('save_button'))
        if hasattr(self, 'delete_btn'):
            self.delete_btn.setText(i18n._('delete_button'))
        if hasattr(self, 'test_btn'):
            self.test_btn.setText(i18n._('test_connection'))
        if hasattr(self, 'import_btn'):
            self.import_btn.setText(i18n._('import_button'))
        if hasattr(self, 'export_btn'):
            self.export_btn.setText(i18n._('export_button'))

        # 重新加载配置列表以更新 [当前使用] 文本
        self.load_configs()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 主面板
        panel = QtWidgets.QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border-radius: 15px;
                border: none;
            }
        """)
        panel_layout = QtWidgets.QVBoxLayout(panel)
        panel_layout.setContentsMargins(25, 25, 25, 25)
        panel_layout.setSpacing(15)

        # 已保存的配置列表
        self.labels['list_label'] = QtWidgets.QLabel(i18n._('saved_configs'))
        self.labels['list_label'].setStyleSheet("color: #CCCCCC; font-size: 14px;")
        panel_layout.addWidget(self.labels['list_label'])
        
        self.config_list = QtWidgets.QListWidget()
        self.config_list.setMaximumHeight(120)
        self.config_list.setStyleSheet("""
            QListWidget {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #5DADE2;
                color: #2D2D2D;
            }
            QListWidget::item:hover {
                background-color: #555555;
            }
        """)
        self.config_list.itemClicked.connect(self.on_config_selected)
        panel_layout.addWidget(self.config_list)
        
        # 配置表单
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(12)
        
        def create_line_edit(placeholder=""):
            edit = QtWidgets.QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setStyleSheet("""
                QLineEdit {
                    background-color: #4A4A4A;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    padding: 10px 15px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 2px solid #5DADE2;
                }
            """)
            return edit
        
        self.name_edit = create_line_edit("e.g., SiliconFlow, OpenAI")
        form_layout.addRow(self.create_label(i18n._('name'), 'name_label'), self.name_edit)

        self.url_edit = create_line_edit("https://api.example.com/v1")
        form_layout.addRow(self.create_label(i18n._('api_url'), 'url_label'), self.url_edit)

        self.key_edit = create_line_edit("sk-...")
        self.key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow(self.create_label(i18n._('api_key'), 'key_label'), self.key_edit)

        self.model_edit = create_line_edit("e.g., gpt-4, deepseek-chat")
        form_layout.addRow(self.create_label(i18n._('model'), 'model_label'), self.model_edit)
        
        # 复选框
        checkbox_style = """
            QCheckBox {
                color: #CCCCCC;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: none;
                background-color: #4A4A4A;
            }
            QCheckBox::indicator:checked {
                background-color: #5DADE2;
            }
        """
        
        self.reasoning_checkbox = QtWidgets.QCheckBox(i18n._('reasoning_model'))
        self.reasoning_checkbox.setStyleSheet(checkbox_style)
        form_layout.addRow("", self.reasoning_checkbox)
        
        self.current_checkbox = QtWidgets.QCheckBox(i18n._('set_as_current'))
        self.current_checkbox.setStyleSheet(checkbox_style)
        form_layout.addRow("", self.current_checkbox)
        
        panel_layout.addLayout(form_layout)
        
        # 按钮区域
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.new_btn = StyledButton(i18n._('new_button'))
        self.new_btn.clicked.connect(self.on_new)
        btn_layout.addWidget(self.new_btn)
        
        self.save_btn = StyledButton(i18n._('save_button'))
        self.save_btn.clicked.connect(self.on_save)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = StyledButton(i18n._('delete_button'))
        self.delete_btn.clicked.connect(self.on_delete)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        self.test_btn = StyledButton(i18n._('test_connection'))
        self.test_btn.clicked.connect(self.on_test)
        btn_layout.addWidget(self.test_btn)
        
        panel_layout.addLayout(btn_layout)
        
        # 导入导出
        io_layout = QtWidgets.QHBoxLayout()
        io_layout.setSpacing(10)
        
        self.import_btn = StyledButton(i18n._('import_button'))
        self.import_btn.clicked.connect(self.on_import)
        io_layout.addWidget(self.import_btn)
        
        self.export_btn = StyledButton(i18n._('export_button'))
        self.export_btn.clicked.connect(self.on_export)
        io_layout.addWidget(self.export_btn)
        
        io_layout.addStretch()
        panel_layout.addLayout(io_layout)
        
        panel_layout.addStretch()
        layout.addWidget(panel)
    
    def create_label(self, text, key=None):
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("color: #CCCCCC; font-size: 14px;")
        if key:
            self.labels[key] = label
        return label
    
    def load_configs(self):
        self.config_list.clear()
        current = config.config_manager.get_current_config()
        current_name = current.get('name') if current else None
        
        for cfg in config.config_manager.get_all_configs():
            name = cfg.get('name', '')
            display = name
            if name == current_name:
                display = "%s %s" % (name, i18n._('current_use'))
            self.config_list.addItem(display)
        
        if current_name:
            self.load_config_to_form(current)
    
    def on_config_selected(self, item):
        name = item.text().replace(" %s" % i18n._('current_use'), "")
        cfg = config.config_manager.get_config(name)
        if cfg:
            self.load_config_to_form(cfg)
    
    def load_config_to_form(self, cfg):
        self.current_config_name = cfg.get('name')
        self.name_edit.setText(cfg.get('name', ''))
        self.url_edit.setText(cfg.get('api_url', ''))
        self.key_edit.setText(cfg.get('api_key', ''))
        self.model_edit.setText(cfg.get('model', ''))
        self.reasoning_checkbox.setChecked(cfg.get('is_reasoning_model', False))
        
        current = config.config_manager.get_current_config()
        self.current_checkbox.setChecked(
            current and current.get('name') == cfg.get('name')
        )
    
    def clear_form(self):
        self.current_config_name = None
        self.name_edit.clear()
        self.url_edit.clear()
        self.key_edit.clear()
        self.model_edit.clear()
        self.reasoning_checkbox.setChecked(False)
        self.current_checkbox.setChecked(False)
    
    def on_new(self):
        self.clear_form()
        self.config_list.clearSelection()
    
    def on_save(self):
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        key = self.key_edit.text().strip()
        model = self.model_edit.text().strip()
        
        if not name:
            self.show_warning(i18n._('name_required'))
            return
        if not url:
            self.show_warning(i18n._('url_required'))
            return
        if not key:
            self.show_warning(i18n._('key_required'))
            return
        if not model:
            self.show_warning(i18n._('model_required'))
            return
        
        cfg = {
            'name': name,
            'api_url': url,
            'api_key': key,
            'model': model,
            'is_reasoning_model': self.reasoning_checkbox.isChecked()
        }
        
        if config.config_manager.add_config(cfg):
            self.show_info(i18n._('save_success'))
            if self.current_checkbox.isChecked():
                config.config_manager.set_current_config(name)
                ai_client.ai_client.set_config(cfg)
            self.load_configs()
            self.config_changed.emit()
        else:
            self.show_error("Failed to save configuration")
    
    def on_delete(self):
        name = self.name_edit.text().strip()
        if not name:
            self.show_warning(i18n._('select_config_first'))
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm", i18n._('confirm_delete', name),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if config.config_manager.delete_config(name):
                self.show_info(i18n._('delete_success'))
                self.clear_form()
                self.load_configs()
                self.config_changed.emit()
    
    def on_test(self):
        url = self.url_edit.text().strip()
        key = self.key_edit.text().strip()
        model = self.model_edit.text().strip()
        
        if not url or not key or not model:
            self.show_warning(i18n._('error_no_config'))
            return
        
        temp_client = ai_client.AIClient()
        temp_client.set_config({
            'api_url': url,
            'api_key': key,
            'model': model
        })
        
        success, msg = temp_client.test_connection()
        if success:
            self.show_info(i18n._('test_success'))
        else:
            self.show_error(i18n._('test_failed', msg))
    
    def on_import(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            if config.config_manager.import_configs(filename):
                self.show_info("Configurations imported successfully")
                self.load_configs()
                self.config_changed.emit()
            else:
                self.show_error("Failed to import configurations")
    
    def on_export(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Configuration", "pymol_ai_config.json", "JSON Files (*.json)"
        )
        if filename:
            if config.config_manager.export_configs(filename):
                self.show_info("Configurations exported successfully")
            else:
                self.show_error("Failed to export configurations")
    
    def show_info(self, msg):
        QtWidgets.QMessageBox.information(self, "Success", msg)
    
    def show_warning(self, msg):
        QtWidgets.QMessageBox.warning(self, "Warning", msg)
    
    def show_error(self, msg):
        QtWidgets.QMessageBox.critical(self, "Error", msg)


class LogWidget(QtWidgets.QWidget):
    """日志标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_logs()
        logger.logger.add_observer(self.on_log_entry)

    def update_language(self):
        """更新界面语言"""
        if hasattr(self, 'category_label'):
            self.category_label.setText(i18n._('log_category'))
        if hasattr(self, 'auto_scroll'):
            self.auto_scroll.setText(i18n._('auto_scroll'))
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setText(i18n._('clear_log'))

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 控制栏
        control_panel = QtWidgets.QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border-radius: 12px;
                border: none;
            }
        """)
        control_layout = QtWidgets.QHBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 10, 15, 10)
        
        # 日志类别过滤
        category_label = QtWidgets.QLabel(i18n._('log_category'))
        category_label.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        control_layout.addWidget(category_label)
        
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem("All", None)
        self.category_combo.addItem("[USER_INPUT]", logger.USER_INPUT)
        self.category_combo.addItem("[AI_REQUEST]", logger.AI_REQUEST)
        self.category_combo.addItem("[AI_RESPONSE]", logger.AI_RESPONSE)
        self.category_combo.addItem("[TOOL_CALL]", logger.TOOL_CALL)
        self.category_combo.addItem("[ERRORS]", logger.ERRORS)
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 120px;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #FFFFFF;
                selection-background-color: #5DADE2;
                border: none;
            }
        """)
        self.category_combo.currentIndexChanged.connect(self.on_filter_changed)
        control_layout.addWidget(self.category_combo)
        
        control_layout.addStretch()
        
        # 自动滚动
        self.auto_scroll = QtWidgets.QCheckBox(i18n._('auto_scroll'))
        self.auto_scroll.setChecked(True)
        self.auto_scroll.setStyleSheet("""
            QCheckBox {
                color: #CCCCCC;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: none;
                background-color: #4A4A4A;
            }
            QCheckBox::indicator:checked {
                background-color: #5DADE2;
            }
        """)
        control_layout.addWidget(self.auto_scroll)
        
        # 清空按钮
        self.clear_btn = StyledButton(i18n._('clear_log'))
        self.clear_btn.setFixedSize(85, 30)
        self.clear_btn.clicked.connect(self.on_clear)
        control_layout.addWidget(self.clear_btn)
        
        layout.addWidget(control_panel)
        
        # 日志显示区域
        log_panel = QtWidgets.QFrame()
        log_panel.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border-radius: 15px;
                border: none;
            }
        """)
        log_layout = QtWidgets.QVBoxLayout(log_panel)
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_panel, stretch=1)
    
    def load_logs(self):
        self.log_text.clear()
        category = self.category_combo.currentData()
        logs = logger.logger.get_logs(category=category, limit=500)
        
        for entry in logs:
            self.append_log_entry(entry)
    
    def append_log_entry(self, entry):
        timestamp = entry.get('timestamp', '')[:19]
        category = entry.get('category', 'UNKNOWN')
        message = entry.get('message', '')
        data = entry.get('data')
        
        # 根据类别设置颜色
        colors = {
            'USER_INPUT': '#58D68D',    # 绿色
            'AI_REQUEST': '#5DADE2',    # 蓝色
            'AI_RESPONSE': '#AF7AC5',   # 紫色
            'TOOL_CALL': '#F5B041',     # 黄色
            'ERRORS': '#F07178',        # 红色
        }
        color = colors.get(category, '#FFFFFF')
        
        # 构建日志行
        log_line = '<span style="color: #888888">[%s]</span> ' % timestamp
        log_line += '<span style="color: %s">[%s]</span> ' % (color, category)
        log_line += '%s' % message.replace("<", "&lt;").replace(">", "&gt;")
        
        # 如果有数据，格式化显示
        if data:
            try:
                if isinstance(data, dict):
                    data_str = json.dumps(data, ensure_ascii=False, indent=2)
                else:
                    data_str = str(data)
                data_str = data_str.replace("<", "&lt;").replace(">", "&gt;")
                # 限制数据长度
                if len(data_str) > 500:
                    data_str = data_str[:500] + "... [truncated]"
                log_line += '<br><span style="color: #888888; margin-left: 20px; font-size: 11px;">%s</span>' % data_str.replace('\n', '<br>')
            except:
                pass
        
        log_line += '<br>'
        
        self.log_text.insertHtml(log_line)
        
        if self.auto_scroll.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def on_log_entry(self, entry):
        QtCore.QTimer.singleShot(0, lambda: self.handle_new_entry(entry))
    
    def handle_new_entry(self, entry):
        category_filter = self.category_combo.currentData()
        if category_filter and entry.get('category') != category_filter:
            return
        self.append_log_entry(entry)
    
    def on_filter_changed(self):
        self.load_logs()
    
    def on_clear(self):
        logger.logger.clear()
        self.log_text.clear()
    
    def __del__(self):
        try:
            logger.logger.remove_observer(self.on_log_entry)
        except:
            pass


class AboutDialog(QtWidgets.QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n._('about_title'))
        self.setFixedSize(400, 500)
        self.setup_ui()
    
    def setup_ui(self):
        # 深色主题样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D2D;
            }
            QLabel {
                color: #CCCCCC;
                background-color: transparent;
            }
            QPushButton {
                background-color: #5DADE2;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #76C5F0;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        
        # 标题
        title_label = QtWidgets.QLabel("🤖 PyMOL AI Assistant")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #5DADE2;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本号
        version_label = QtWidgets.QLabel("%s %s" % (i18n._('about_version'), __version__))
        version_label.setStyleSheet("font-size: 14px; color: #888888;")
        version_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        # 插件介绍
        intro_text = QtWidgets.QLabel(i18n._('about_intro'))
        intro_text.setStyleSheet("font-size: 12px; color: #CCCCCC; line-height: 1.6;")
        intro_text.setAlignment(QtCore.Qt.AlignLeft)
        intro_text.setWordWrap(True)
        layout.addWidget(intro_text)
        
        layout.addSpacing(20)
        
        # 作者信息
        info_widget = QtWidgets.QWidget()
        info_layout = QtWidgets.QFormLayout(info_widget)
        info_layout.setSpacing(8)
        info_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        
        author_label = QtWidgets.QLabel("Mo Qiqin")
        author_label.setStyleSheet("color: #CCCCCC;")
        info_layout.addRow(i18n._('about_author') + ":", author_label)
        
        email_label = QtWidgets.QLabel("moqiqin@live.com")
        email_label.setStyleSheet("color: #5DADE2;")
        info_layout.addRow(i18n._('about_email') + ":", email_label)
        
        # GitHub 链接
        github_link = QtWidgets.QLabel(
            "<a href='https://github.com/Masterchiefm/pymol-ai-assistant' "
            "style='color: #5DADE2; text-decoration: none;'>GitHub</a>"
        )
        github_link.setOpenExternalLinks(True)
        github_link.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        info_layout.addRow(i18n._('about_github') + ":", github_link)
        
        layout.addWidget(info_widget)
        layout.addStretch()
        
        # 捐赠按钮
        donate_btn = QtWidgets.QPushButton(i18n._('about_donate'))
        donate_btn.setStyleSheet("""
            QPushButton {
                background-color: #D4A574;
                color: #2D2D2D;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E4B584;
            }
        """)
        donate_btn.clicked.connect(self.show_donate)
        layout.addWidget(donate_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton(i18n._('about_close'))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)
    
    def show_donate(self):
        """显示捐赠二维码"""
        donate_dialog = QtWidgets.QDialog(self)
        donate_dialog.setWindowTitle(i18n._('donate_title'))
        donate_dialog.setFixedSize(350, 400)
        donate_dialog.setStyleSheet("""
            QDialog {
                background-color: #2D2D2D;
            }
            QLabel {
                color: #CCCCCC;
                background-color: transparent;
            }
            QPushButton {
                background-color: #404040;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)

        layout = QtWidgets.QVBoxLayout(donate_dialog)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        # 提示文字
        hint_label = QtWidgets.QLabel(i18n._('donate_hint'))
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(hint_label)
        
        layout.addSpacing(10)
        
        # 加载二维码图片
        qr_path = os.path.join(os.path.dirname(__file__), "fig", "donate.png")
        
        qr_label = QtWidgets.QLabel()
        if os.path.exists(qr_path):
            pixmap = QtGui.QPixmap(qr_path)
            scaled_pixmap = pixmap.scaled(280, 280, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            qr_label.setPixmap(scaled_pixmap)
        else:
            qr_label.setText(i18n._('donate_qr_missing'))
            qr_label.setStyleSheet("color: #E74C3C; font-size: 12px;")
        qr_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(qr_label)
        
        layout.addSpacing(10)
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton(i18n._('about_close'))
        close_btn.clicked.connect(donate_dialog.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)
        
        donate_dialog.exec_()


class AIAssistantDialog(QtWidgets.QDialog):
    """AI助手主对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n._('window_title'))
        # 默认大小500x360（比之前小10%），不设置最小大小限制
        self.resize(500, 360)
        # 启用最大化、最小化和关闭按钮
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowMinimizeButtonHint)

        # 设置深色背景
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D2D;
            }
        """)

        # 添加语言变更回调
        i18n.add_language_change_callback(self._on_language_changed)

        self.setup_ui()
        self.init_ai_client()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建菜单栏
        self.setup_menu_bar()
        layout.addLayout(self._menu_layout)
        
        # 创建QTabWidget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(False)
        # 设置标签位置在上方
        self.tabs.setTabPosition(QtWidgets.QTabWidget.North)
        # 获取TabBar并设置居中对齐
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setElideMode(QtCore.Qt.ElideNone)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
                top: 0px;
            }
            QTabBar {
                qproperty-alignment: AlignCenter;
                background: transparent;
                border: none;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #AAAAAA;
                border: none;
                border-radius: 12px;
                padding: 6px 25px;
                margin-right: 10px;
                margin-top: 5px;
                margin-bottom: 5px;
                font-size: 13px;
                min-width: 60px;
            }
            QTabBar::tab:selected {
                background-color: #5DADE2;
                color: #FFFFFF;
            }
            QTabBar::tab:hover:!selected {
                background-color: #4A4A4A;
                color: #CCCCCC;
            }
        """)
        
        # 聊天标签页
        self.chat_widget = ChatWidget()
        self.chat_widget.message_sent.connect(self.on_message_sent)
        self.chat_widget.stop_requested.connect(self.on_stop_requested)
        self.tabs.addTab(self.chat_widget, i18n._('tab_chat'))
        
        # 配置标签页
        self.config_widget = ConfigWidget()
        self.config_widget.config_changed.connect(self.on_config_changed)
        self.tabs.addTab(self.config_widget, i18n._('tab_config'))
        
        # 日志标签页
        self.log_widget = LogWidget()
        self.tabs.addTab(self.log_widget, i18n._('tab_log'))
        
        layout.addWidget(self.tabs)
    
    def setup_menu_bar(self):
        """设置菜单栏"""
        # 创建水平布局放置菜单按钮
        menu_layout = QtWidgets.QHBoxLayout()
        menu_layout.setSpacing(10)

        # 语言切换按钮 - 点击直接切换语言
        self.lang_btn = StyledButton("🌐 " + self._get_target_language_text())
        self.lang_btn.setFixedHeight(32)
        self.lang_btn.clicked.connect(self.toggle_language)
        menu_layout.addWidget(self.lang_btn)

        menu_layout.addStretch()
        
        # 关于按钮
        self.about_btn = StyledButton("ℹ️ " + i18n._('menu_about'))
        self.about_btn.setFixedHeight(32)
        self.about_btn.clicked.connect(self.show_about_dialog)
        menu_layout.addWidget(self.about_btn)
        
        # 将菜单布局添加到主布局
        # 注意：这里我们暂时不添加，因为setup_ui中还没有获取到layout
        # 我们将在setup_ui中使用这个方法
        self._menu_layout = menu_layout
    
    def _get_target_language_text(self):
        """获取目标语言文本（显示当前语言对应的目标语言）"""
        if i18n.get_language() == 'zh':
            return 'English'
        else:
            return '中文'

    def toggle_language(self):
        """点击切换语言"""
        current_lang = i18n.get_language()
        new_lang = 'en' if current_lang == 'zh' else 'zh'
        i18n.set_language(new_lang)
        config.config_manager.set_language(new_lang)

    def _on_language_changed(self, lang):
        """语言变更回调 - 更新所有UI文本"""
        # 更新窗口标题
        self.setWindowTitle(i18n._('window_title'))

        # 更新语言按钮 - 显示目标语言
        self.lang_btn.setText("🌐 " + self._get_target_language_text())
        self.about_btn.setText("ℹ️ " + i18n._('menu_about'))

        # 更新标签页标题
        self.tabs.setTabText(0, i18n._('tab_chat'))
        self.tabs.setTabText(1, i18n._('tab_config'))
        self.tabs.setTabText(2, i18n._('tab_log'))

        # 更新聊天组件
        self.chat_widget.input_text.setPlaceholderText(i18n._('input_placeholder'))
        self.chat_widget.send_btn.setText(i18n._('send_button') if not self.chat_widget.is_streaming else i18n._('stop_button'))
        self.chat_widget.clear_btn.setText(i18n._('clear_chat'))

        # 更新消息角色标签
        for msg in self.chat_widget.messages:
            role = msg['role']
            widget = msg['widget']
            role_text = {
                'user': i18n._('user'),
                'assistant': i18n._('assistant'),
                'thinking': i18n._('thinking'),
                'tool': i18n._('using_tool'),
                'tool_result': i18n._('tool_result'),
                'tool_error': i18n._('tool_error'),
            }.get(role, role)
            widget.role_label.setText("<b>%s:</b>" % role_text)

        # 更新配置和日志界面
        self.config_widget.update_language()
        self.log_widget.update_language()
    
    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def init_ai_client(self):
        cfg = config.config_manager.get_current_config()
        if cfg:
            ai_client.ai_client.set_config(cfg)
            logger.logger.info(logger.SYSTEM, "AI client initialized", cfg)
    
    def on_message_sent(self, text):
        cfg = config.config_manager.get_current_config()
        if not cfg:
            QtWidgets.QMessageBox.warning(self, i18n._('error_no_config'), i18n._('error_no_config'))
            return
        
        ai_client.ai_client.set_config(cfg)
        
        # 记录用户输入（详细日志）
        logger.logger.info(
            logger.USER_INPUT, 
            "用户发送消息", 
            {"content": text}
        )
        
        messages = self.chat_widget.get_messages_for_api()
        
        # 记录发送到AI服务器的请求
        request_data = {
            "model": cfg.get('model'),
            "messages": messages,
            "stream": True,
            "tools": "enabled"
        }
        logger.logger.info(
            logger.AI_REQUEST,
            "发送到AI服务器的请求",
            request_data
        )
        
        self.worker = AIStreamWorker(messages)
        self.worker.thinking_signal.connect(self.on_thinking)
        self.worker.content_signal.connect(self.on_content)
        self.worker.tool_signal.connect(self.on_tool_call)
        self.worker.error_signal.connect(self.on_error)
        self.worker.finished_signal.connect(self.on_request_finished)
        self.worker.start()
    
    def on_stop_requested(self):
        """用户请求停止"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.chat_widget.set_streaming_state(False)
            self.chat_widget.add_message('assistant', '[已停止]')
    
    def on_thinking(self, text, is_end):
        if is_end:
            self.chat_widget.is_thinking = False
        else:
            if not self.chat_widget.is_thinking:
                self.chat_widget.is_thinking = True
                self.chat_widget.start_message('thinking')
            self.chat_widget.append_to_current(text)
    
    def on_content(self, text, is_end):
        if is_end:
            pass
        else:
            if self.chat_widget.is_thinking:
                self.chat_widget.is_thinking = False
                self.chat_widget.start_message('assistant')
            elif not self.chat_widget.current_message_widget or self.chat_widget.current_message_widget.role != 'assistant':
                self.chat_widget.start_message('assistant')
            self.chat_widget.append_to_current(text)
    
    def on_tool_call(self, tool_name, params, result):
        # 只处理有结果的情况，避免重复显示
        if result is not None:
            self.chat_widget.add_message('tool', "使用工具: %s\n参数: %s\n结果: %s" % (tool_name, params, result))
    
    def on_error(self, error_msg):
        # 记录错误到日志
        logger.logger.error(
            logger.ERRORS,
            "AI请求错误",
            {"error": error_msg}
        )
        self.chat_widget.add_message('assistant', "错误: %s" % error_msg)
        self.chat_widget.set_streaming_state(False)
    
    def on_request_finished(self):
        self.chat_widget.set_streaming_state(False)
    
    def on_config_changed(self):
        self.init_ai_client()


class AIStreamWorker(QtCore.QThread):
    """AI流式请求工作线程"""
    
    thinking_signal = QtCore.Signal(str, bool)
    content_signal = QtCore.Signal(str, bool)
    tool_signal = QtCore.Signal(str, object, object)
    error_signal = QtCore.Signal(str)
    finished_signal = QtCore.Signal()
    
    def __init__(self, messages):
        super().__init__()
        self.messages = messages
        self._is_running = True
    
    def run(self):
        try:
            accumulated_content = ""
            accumulated_thinking = ""
            
            def on_thinking(text, is_end):
                if self._is_running:
                    nonlocal accumulated_thinking
                    accumulated_thinking += text
                    self.thinking_signal.emit(text, is_end)
            
            def on_content(text, is_end):
                if self._is_running:
                    nonlocal accumulated_content
                    accumulated_content += text
                    self.content_signal.emit(text, is_end)
            
            def on_tool_call(tool_name, params, result):
                if self._is_running:
                    self.tool_signal.emit(tool_name, params, result)
            
            def on_error(error_msg):
                if self._is_running:
                    self.error_signal.emit(error_msg)
            
            # 执行流式请求
            for chunk in ai_client.ai_client.chat_stream(
                self.messages,
                on_thinking=on_thinking,
                on_content=on_content,
                on_tool_call=on_tool_call,
                on_error=on_error
            ):
                if not self._is_running:
                    break
            
            # 记录AI服务器的完整响应
            logger.logger.info(
                logger.AI_RESPONSE,
                "AI服务器的完整响应",
                {
                    "thinking": accumulated_thinking,
                    "content": accumulated_content
                }
            )
        
        except Exception as e:
            if self._is_running:
                self.error_signal.emit(str(e))
        
        finally:
            self.finished_signal.emit()
    
    def terminate(self):
        self._is_running = False
        super().terminate()
