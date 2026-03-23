# -*- coding: utf-8 -*-
'''
主模块 - 包含AI助手对话框主界面（深色主题）
'''

import os
import json
from datetime import datetime

from pymol.Qt import QtCore, QtWidgets, QtGui

from . import i18n, config, logger, ai_client, tools, get_update_info, __version__ as PLUGIN_VERSION, markdown_renderer


# 版本号
__version__ = PLUGIN_VERSION


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
            QLabel::item:selected {
                background-color: #3d8bfd;
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
        """设置内容，支持不同颜色的文本和Markdown渲染"""
        self.raw_content = content

        if self.role == 'assistant':
            html_content = markdown_renderer.MarkdownRenderer.render(content)
        else:
            html_content = self._format_text(content)

        self.content_label.setText(html_content)

    def _format_text(self, text):
        """格式化普通文本，支持不同颜色的文本"""
        escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

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

        return '<br>'.join(formatted_lines)
    
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
        self.loading_dots = 0
        self.loading_timer = QtCore.QTimer()
        self.loading_timer.timeout.connect(self._update_loading_animation)
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
        
        # 创建加载指示器（始终在底部）
        self._create_loading_indicator()
        
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
    
    def _update_loading_animation(self):
        """更新加载动画 - 旋转指示器"""
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.loading_dots = (self.loading_dots + 1) % len(spinner_chars)
        spinner = spinner_chars[self.loading_dots]
        
        loading_text = "%s %s" % (spinner, i18n._('loading'))
        self.loading_indicator.set_content(loading_text)
    
    def _create_loading_indicator(self):
        """创建加载指示器（始终在底部）"""
        self.loading_indicator = MessageWidget('thinking', i18n._('loading'))
        self.loading_indicator.hide()
        # 插入到 stretch 之前（最后一个位置）
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.loading_indicator)
    
    def show_loading(self):
        """显示加载指示器"""
        self.loading_indicator.show()
        self.loading_dots = 0
        self.loading_timer.start(80)
        self.scroll_to_bottom()
    
    def hide_loading(self):
        """隐藏加载指示器"""
        self.loading_timer.stop()
        self.loading_indicator.hide()
    
    def add_message(self, role, content):
        """添加消息 - 插入到加载指示器之前"""
        msg_widget = MessageWidget(role, content)
        # 插入到倒数第二个位置（加载指示器之前）
        insert_pos = self.messages_layout.count() - 2
        if insert_pos < 0:
            insert_pos = 0
        self.messages_layout.insertWidget(insert_pos, msg_widget)
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
    """配置标签页 - 支持 LiteLLM 多提供商"""

    config_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config_name = None
        self.labels = {}
        self.setup_ui()
        self.load_configs()

    def update_language(self):
        """更新界面语言"""
        if hasattr(self, 'labels'):
            self.labels.get('list_label').setText(i18n._('saved_configs'))
            self.labels.get('name_label').setText(i18n._('name'))
            self.labels.get('provider_label').setText(i18n._('provider'))
            self.labels.get('url_label').setText(i18n._('api_url'))
            self.labels.get('key_label').setText(i18n._('api_key'))
            self.labels.get('model_label').setText(i18n._('model'))
            self.labels.get('version_label').setText(i18n._('api_version'))
            self.labels.get('temp_label').setText(i18n._('temperature'))
            self.labels.get('tokens_label').setText(i18n._('max_tokens'))
            self.labels.get('timeout_label').setText(i18n._('timeout'))

        if hasattr(self, 'reasoning_checkbox'):
            self.reasoning_checkbox.setText(i18n._('reasoning_model'))
        if hasattr(self, 'current_checkbox'):
            self.current_checkbox.setText(i18n._('set_as_current'))
        if hasattr(self, 'advanced_toggle'):
            self.advanced_toggle.setText(i18n._('show_advanced'))

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

        self.update_provider_combo()
        self.load_configs()

    def update_provider_combo(self):
        """更新提供商下拉框"""
        current_provider = self.provider_combo.currentData()
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        for provider_id in config.get_provider_list():
            provider_info = config.get_provider_info(provider_id)
            self.provider_combo.addItem(provider_info['name'], provider_id)
        idx = self.provider_combo.findData(current_provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.blockSignals(False)

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        panel = QtWidgets.QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border-radius: 15px;
                border: none;
            }
        """)
        panel_layout = QtWidgets.QVBoxLayout(panel)
        panel_layout.setContentsMargins(25, 20, 25, 20)
        panel_layout.setSpacing(12)

        self.labels['list_label'] = QtWidgets.QLabel(i18n._('saved_configs'))
        self.labels['list_label'].setStyleSheet("color: #CCCCCC; font-size: 14px;")
        panel_layout.addWidget(self.labels['list_label'])
        
        self.config_list = QtWidgets.QListWidget()
        self.config_list.setMaximumHeight(80)
        self.config_list.setStyleSheet("""
            QListWidget {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 3px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
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
        
        line_style = """
            QLineEdit {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #5DADE2;
            }
            QLineEdit:disabled {
                background-color: #3A3A3A;
                color: #888888;
            }
        """
        
        combo_style = """
            QComboBox {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #CCCCCC;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #4A4A4A;
                color: #FFFFFF;
                selection-background-color: #5DADE2;
                selection-color: #2D2D2D;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QComboBox:disabled {
                background-color: #3A3A3A;
                color: #888888;
            }
        """
        
        form_layout = QtWidgets.QGridLayout()
        form_layout.setSpacing(10)
        form_layout.setColumnStretch(1, 1)
        
        row = 0
        self.labels['name_label'] = QtWidgets.QLabel(i18n._('name'))
        self.labels['name_label'].setStyleSheet("color: #CCCCCC; font-size: 13px;")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("e.g., My GPT-4")
        self.name_edit.setStyleSheet(line_style)
        form_layout.addWidget(self.labels['name_label'], row, 0)
        form_layout.addWidget(self.name_edit, row, 1)
        
        row += 1
        self.labels['provider_label'] = QtWidgets.QLabel(i18n._('provider'))
        self.labels['provider_label'].setStyleSheet("color: #CCCCCC; font-size: 13px;")
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.setStyleSheet(combo_style)
        for provider_id in config.get_provider_list():
            provider_info = config.get_provider_info(provider_id)
            self.provider_combo.addItem(provider_info['name'], provider_id)
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        form_layout.addWidget(self.labels['provider_label'], row, 0)
        form_layout.addWidget(self.provider_combo, row, 1)

        row += 1
        self.labels['model_label'] = QtWidgets.QLabel(i18n._('model'))
        self.labels['model_label'].setStyleSheet("color: #CCCCCC; font-size: 13px;")
        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setStyleSheet(combo_style)
        form_layout.addWidget(self.labels['model_label'], row, 0)
        form_layout.addWidget(self.model_combo, row, 1)

        row += 1
        self.labels['url_label'] = QtWidgets.QLabel(i18n._('api_url'))
        self.labels['url_label'].setStyleSheet("color: #CCCCCC; font-size: 13px;")
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText(i18n._('api_url_placeholder'))
        self.url_edit.setStyleSheet(line_style)
        form_layout.addWidget(self.labels['url_label'], row, 0)
        form_layout.addWidget(self.url_edit, row, 1)

        row += 1
        self.labels['key_label'] = QtWidgets.QLabel(i18n._('api_key'))
        self.labels['key_label'].setStyleSheet("color: #CCCCCC; font-size: 13px;")
        self.key_edit = QtWidgets.QLineEdit()
        self.key_edit.setPlaceholderText(i18n._('api_key_placeholder'))
        self.key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.key_edit.setStyleSheet(line_style)
        form_layout.addWidget(self.labels['key_label'], row, 0)
        form_layout.addWidget(self.key_edit, row, 1)

        row += 1
        self.labels['version_label'] = QtWidgets.QLabel(i18n._('api_version'))
        self.labels['version_label'].setStyleSheet("color: #CCCCCC; font-size: 13px;")
        self.version_edit = QtWidgets.QLineEdit()
        self.version_edit.setPlaceholderText(i18n._('api_version_placeholder'))
        self.version_edit.setStyleSheet(line_style)
        form_layout.addWidget(self.labels['version_label'], row, 0)
        form_layout.addWidget(self.version_edit, row, 1)
        
        panel_layout.addLayout(form_layout)
        
        checkbox_style = """
            QCheckBox {
                color: #CCCCCC;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: none;
                background-color: #4A4A4A;
            }
            QCheckBox::indicator:checked {
                background-color: #5DADE2;
            }
        """
        
        self.reasoning_checkbox = QtWidgets.QCheckBox(i18n._('reasoning_model'))
        self.reasoning_checkbox.setStyleSheet(checkbox_style)
        form_layout.addWidget(self.reasoning_checkbox, row, 0, 1, 2)
        
        row += 1
        self.current_checkbox = QtWidgets.QCheckBox(i18n._('set_as_current'))
        self.current_checkbox.setStyleSheet(checkbox_style)
        form_layout.addWidget(self.current_checkbox, row, 0, 1, 2)
        
        panel_layout.addLayout(form_layout)

        self.advanced_toggle = QtWidgets.QPushButton(i18n._('show_advanced'))
        self.advanced_toggle.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #5DADE2;
                border: none;
                font-size: 12px;
                text-align: left;
                padding: 3px 0;
            }
            QPushButton:hover {
                color: #7EC8E3;
            }
        """)
        self.advanced_toggle.clicked.connect(self.toggle_advanced)
        panel_layout.addWidget(self.advanced_toggle)

        self.advanced_frame = QtWidgets.QFrame()
        self.advanced_frame.setStyleSheet("QFrame { background: transparent; }")
        advanced_layout = QtWidgets.QGridLayout(self.advanced_frame)
        advanced_layout.setSpacing(8)
        advanced_layout.setColumnStretch(1, 1)
        
        spin_style = """
            QSpinBox, QDoubleSpinBox {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """
        
        self.labels['temp_label'] = QtWidgets.QLabel(i18n._('temperature'))
        self.labels['temp_label'].setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.temp_spin = QtWidgets.QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.7)
        self.temp_spin.setStyleSheet(spin_style)
        advanced_layout.addWidget(self.labels['temp_label'], 0, 0)
        advanced_layout.addWidget(self.temp_spin, 0, 1)

        self.labels['tokens_label'] = QtWidgets.QLabel(i18n._('max_tokens'))
        self.labels['tokens_label'].setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.max_tokens_spin = QtWidgets.QSpinBox()
        self.max_tokens_spin.setRange(100, 128000)
        self.max_tokens_spin.setSingleStep(100)
        self.max_tokens_spin.setValue(4096)
        self.max_tokens_spin.setStyleSheet(spin_style)
        advanced_layout.addWidget(self.labels['tokens_label'], 1, 0)
        advanced_layout.addWidget(self.max_tokens_spin, 1, 1)

        self.labels['timeout_label'] = QtWidgets.QLabel(i18n._('timeout'))
        self.labels['timeout_label'].setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.timeout_spin = QtWidgets.QSpinBox()
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setSingleStep(10)
        self.timeout_spin.setValue(60)
        self.timeout_spin.setStyleSheet(spin_style)
        advanced_layout.addWidget(self.labels['timeout_label'], 2, 0)
        advanced_layout.addWidget(self.timeout_spin, 2, 1)
        
        self.advanced_frame.hide()
        panel_layout.addWidget(self.advanced_frame)
        
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(8)
        
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
        
        io_layout = QtWidgets.QHBoxLayout()
        io_layout.setSpacing(8)
        
        self.import_btn = StyledButton(i18n._('import_button'))
        self.import_btn.clicked.connect(self.on_import)
        io_layout.addWidget(self.import_btn)
        
        self.export_btn = StyledButton(i18n._('export_button'))
        self.export_btn.clicked.connect(self.on_export)
        io_layout.addWidget(self.export_btn)
        
        io_layout.addStretch()
        panel_layout.addLayout(io_layout)
        
        main_layout.addWidget(panel)
        main_layout.addStretch()

        self.on_provider_changed(0)
    
    def toggle_advanced(self):
        """切换高级设置显示"""
        if self.advanced_frame.isVisible():
            self.advanced_frame.hide()
            self.advanced_toggle.setText(i18n._('show_advanced'))
        else:
            self.advanced_frame.show()
            self.advanced_toggle.setText(i18n._('hide_advanced'))
    
    def on_provider_changed(self, index):
        """提供商改变时更新模型列表和表单"""
        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return
            
        provider_info = config.get_provider_info(provider_id)
        
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        models = provider_info.get('models', [])
        for model in models:
            self.model_combo.addItem(model)
        self.model_combo.blockSignals(False)
        
        default_url = provider_info.get('api_base', '')
        if default_url:
            self.url_edit.setText(default_url)
        
        requires_key = provider_info.get('requires_api_key', True)
        requires_base = provider_info.get('requires_api_base', False)
        requires_version = provider_info.get('requires_api_version', False)
        
        self.key_edit.setEnabled(requires_key)
        if not requires_key:
            self.key_edit.setText("not-required")
        elif self.key_edit.text() == "not-required":
            self.key_edit.clear()
        
        self.url_edit.setEnabled(requires_base or provider_id == 'custom')
        self.version_edit.setEnabled(requires_version)
        self.version_edit.setVisible(requires_version)
        self.labels['version_label'].setVisible(requires_version)
    
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
        
        provider_id = cfg.get('provider', 'custom')
        idx = self.provider_combo.findData(provider_id)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        
        self.url_edit.setText(cfg.get('api_url', ''))
        self.key_edit.setText(cfg.get('api_key', ''))
        
        model = cfg.get('model', '')
        model_idx = self.model_combo.findText(model)
        if model_idx >= 0:
            self.model_combo.setCurrentIndex(model_idx)
        else:
            self.model_combo.setEditText(model)
        
        self.version_edit.setText(cfg.get('api_version', ''))
        self.reasoning_checkbox.setChecked(cfg.get('is_reasoning_model', False))
        self.temp_spin.setValue(cfg.get('temperature', 0.7))
        self.max_tokens_spin.setValue(cfg.get('max_tokens', 4096))
        self.timeout_spin.setValue(cfg.get('timeout', 60))
        
        current = config.config_manager.get_current_config()
        self.current_checkbox.setChecked(
            current and current.get('name') == cfg.get('name')
        )
    
    def clear_form(self):
        self.current_config_name = None
        self.name_edit.clear()
        self.provider_combo.setCurrentIndex(0)
        self.url_edit.clear()
        self.key_edit.clear()
        self.model_combo.setEditText('')
        self.version_edit.clear()
        self.reasoning_checkbox.setChecked(False)
        self.current_checkbox.setChecked(False)
        self.temp_spin.setValue(0.7)
        self.max_tokens_spin.setValue(4096)
        self.timeout_spin.setValue(60)
    
    def on_new(self):
        self.clear_form()
        self.config_list.clearSelection()
    
    def on_save(self):
        name = self.name_edit.text().strip()
        provider_id = self.provider_combo.currentData()
        url = self.url_edit.text().strip()
        key = self.key_edit.text().strip()
        model = self.model_combo.currentText().strip()
        
        if not name:
            self.show_warning(i18n._('name_required'))
            return
        if not model:
            self.show_warning(i18n._('model_required'))
            return
        
        provider_info = config.get_provider_info(provider_id)
        if provider_info.get('requires_api_key', True) and not key:
            self.show_warning(i18n._('key_required'))
            return
        
        cfg = {
            'name': name,
            'provider': provider_id,
            'api_url': url,
            'api_key': key,
            'model': model,
            'api_version': self.version_edit.text().strip(),
            'is_reasoning_model': self.reasoning_checkbox.isChecked(),
            'temperature': self.temp_spin.value(),
            'max_tokens': self.max_tokens_spin.value(),
            'timeout': self.timeout_spin.value(),
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
        provider_id = self.provider_combo.currentData()
        url = self.url_edit.text().strip()
        key = self.key_edit.text().strip()
        model = self.model_combo.currentText().strip()
        
        if not model:
            self.show_warning(i18n._('error_no_config'))
            return
        
        provider_info = config.get_provider_info(provider_id)
        if provider_info.get('requires_api_key', True) and not key:
            self.show_warning(i18n._('error_no_config'))
            return
        
        temp_client = ai_client.AIClient()
        temp_client.set_config({
            'provider': provider_id,
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

        # 设置深色背景和全局样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D2D;
            }
            QMenu {
                background-color: #404040;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 30px 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #5DADE2;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 4px 10px;
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

        # 更新提示按钮（如果有更新）
        self.update_btn = None
        update_info = get_update_info()
        if update_info.get('has_update'):
            self.update_btn = StyledButton("⬆️ " + ("Update" if i18n.get_language() == 'en' else "更新"), accent=True)
            self.update_btn.setFixedHeight(32)
            self.update_btn.clicked.connect(self.show_update_dialog)
            menu_layout.addWidget(self.update_btn)

        # 关于按钮
        self.about_btn = StyledButton("ℹ️ " + i18n._('menu_about'))
        self.about_btn.setFixedHeight(32)
        self.about_btn.clicked.connect(self.show_about_dialog)
        menu_layout.addWidget(self.about_btn)

        # 将菜单布局添加到主布局
        # 注意：这里我们暂时不添加，因为setup_ui中还没有获取到layout
        # 我们将在setup_ui中使用这个方法
        self._menu_layout = menu_layout

    def show_update_dialog(self):
        """显示更新对话框"""
        from . import get_update_info
        update_info = get_update_info()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(i18n._('update_title') if hasattr(i18n, '_') and i18n._('update_title') != 'update_title' else ("Update Available" if i18n.get_language() == 'en' else "发现新版本"))
        dialog.setFixedSize(450, 350)

        # 深色主题样式
        dialog.setStyleSheet("""
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

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        # 标题
        is_en = i18n.get_language() == 'en'
        title_text = "⬆️ New Version Available" if is_en else "⬆️ 发现新版本"
        title_label = QtWidgets.QLabel(title_text)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #5DADE2;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # 版本信息
        current_ver = update_info.get('current_version', 'Unknown')
        latest_ver = update_info.get('latest_version', 'Unknown')
        version_text = f"v{current_ver} → v{latest_ver}" if is_en else f"当前: v{current_ver} → 新版: v{latest_ver}"
        version_label = QtWidgets.QLabel(version_text)
        version_label.setStyleSheet("font-size: 14px; color: #888888;")
        version_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(version_label)

        layout.addSpacing(20)

        # 提示信息
        hint_text = (
            "A new version of PyMOL AI Assistant is available.\n\n"
            "Please uninstall the old version before installing the new one.\n\n"
            "Click the button below to download the latest version:"
        ) if is_en else (
            "PyMOL AI Assistant 有新版本可用。\n\n"
            "请在安装新版前卸载旧版本。\n\n"
            "点击下方按钮下载最新版本："
        )
        hint_label = QtWidgets.QLabel(hint_text)
        hint_label.setStyleSheet("font-size: 13px; color: #CCCCCC; line-height: 1.6;")
        hint_label.setAlignment(QtCore.Qt.AlignLeft)
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        layout.addStretch()

        # 下载按钮
        download_btn = QtWidgets.QPushButton("Download" if is_en else "前往下载")
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #58D68D;
                color: #2D2D2D;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #76E8A0;
            }
        """)
        download_btn.clicked.connect(lambda: self.open_update_page_and_close(dialog))
        layout.addWidget(download_btn, alignment=QtCore.Qt.AlignCenter)

        layout.addSpacing(10)

        # 关闭按钮
        close_btn = QtWidgets.QPushButton("Later" if is_en else "稍后")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)

        dialog.exec_()

    def open_update_page_and_close(self, dialog):
        """打开更新页面并关闭对话框"""
        import webbrowser
        # 根据语言选择对应的更新页面
        if i18n.get_language() == 'zh':
            url = "https://gitee.com/MasterChiefm/pymol-ai-assistant/releases"
        else:
            url = "https://github.com/Masterchiefm/pymol-ai-assistant/releases/latest"
        webbrowser.open(url)
        dialog.accept()
    
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

        # 更新更新按钮文本
        if self.update_btn:
            self.update_btn.setText("⬆️ " + ("Update" if lang == 'en' else "更新"))

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
            "stream": False,
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
        
        # 显示加载指示器
        self.chat_widget.show_loading()
    
    def on_stop_requested(self):
        """用户请求停止"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.chat_widget.hide_loading()
            self.chat_widget.set_streaming_state(False)
            self.chat_widget.add_message('assistant', '[已停止]')
    
    def on_thinking(self, text, is_end):
        # 显示 reasoning content
        if text:
            if not self.chat_widget.is_thinking:
                self.chat_widget.is_thinking = True
                self.chat_widget.start_message('thinking')
            self.chat_widget.append_to_current(text)
        if is_end:
            self.chat_widget.is_thinking = False
    
    def on_content(self, text, is_end):
        if text:
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
        self.chat_widget.hide_loading()
        self.chat_widget.set_streaming_state(False)
    
    def on_request_finished(self):
        self.chat_widget.hide_loading()
        self.chat_widget.set_streaming_state(False)
    
    def on_config_changed(self):
        self.init_ai_client()


class AIStreamWorker(QtCore.QThread):
    """AI请求工作线程 - 非流式调用"""
    
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
            
            result = ai_client.ai_client.chat(
                self.messages,
                on_thinking=on_thinking,
                on_content=on_content,
                on_tool_call=on_tool_call,
                on_error=on_error
            )
            
            logger.logger.info(
                logger.AI_RESPONSE,
                "AI服务器的完整响应",
                {
                    "thinking": accumulated_thinking,
                    "content": accumulated_content,
                    "final_result": result
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
