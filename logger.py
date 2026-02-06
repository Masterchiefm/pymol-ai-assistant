# -*- coding: utf-8 -*-
'''
日志管理模块
'''

import os
import json
import time
from datetime import datetime
from . import i18n as _i18n

# 日志文件路径
LOG_FILE = os.path.join(os.path.expanduser('~'), '.pymol_ai_assistant_log.json')

# 日志级别
DEBUG = 'DEBUG'
INFO = 'INFO'
WARNING = 'WARNING'
ERROR = 'ERROR'

# 日志分类
USER_INPUT = 'USER_INPUT'
AI_REQUEST = 'AI_REQUEST'
AI_RESPONSE = 'AI_RESPONSE'
TOOL_CALL = 'TOOL_CALL'
ERRORS = 'ERRORS'
SYSTEM = 'SYSTEM'


class Logger:
    """日志管理器"""
    
    _instance = None
    _max_entries = 1000  # 最大日志条目数
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._logs = []
        self._observers = []
        self.load()
        self._initialized = True
    
    def add_observer(self, callback):
        """添加日志观察者"""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback):
        """移除日志观察者"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, entry):
        """通知所有观察者"""
        for callback in self._observers:
            try:
                callback(entry)
            except:
                pass
    
    def load(self):
        """从文件加载日志"""
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    self._logs = json.load(f)
            except Exception as e:
                print("[PyMOL AI Assistant] 加载日志失败: {}".format(e))
                self._logs = []
    
    def save(self):
        """保存日志到文件"""
        try:
            # 只保留最近的最大条目数
            logs_to_save = self._logs[-self._max_entries:] if len(self._logs) > self._max_entries else self._logs
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs_to_save, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("[PyMOL AI Assistant] 保存日志失败: {}".format(e))
            return False
    
    def log(self, level, category, message, data=None):
        """
        记录日志
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
            category: 日志类别 (USER_INPUT, AI_REQUEST, AI_RESPONSE, TOOL_CALL, ERRORS)
            message: 日志消息
            data: 附加数据（可选）
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'category': category,
            'message': message,
        }
        
        if data is not None:
            # 序列化数据，避免无法JSON序列化的对象
            try:
                # 尝试序列化，如果失败则转为字符串
                json.dumps(data)
                entry['data'] = data
            except:
                entry['data'] = str(data)
        
        self._logs.append(entry)
        
        # 限制日志大小
        if len(self._logs) > self._max_entries * 1.5:
            self._logs = self._logs[-self._max_entries:]
        
        # 通知观察者
        self._notify_observers(entry)
        
        return entry
    
    def debug(self, category, message, data=None):
        """记录DEBUG级别日志"""
        return self.log(DEBUG, category, message, data)
    
    def info(self, category, message, data=None):
        """记录INFO级别日志"""
        return self.log(INFO, category, message, data)
    
    def warning(self, category, message, data=None):
        """记录WARNING级别日志"""
        return self.log(WARNING, category, message, data)
    
    def error(self, category, message, data=None):
        """记录ERROR级别日志"""
        return self.log(ERROR, category, message, data)
    
    def get_logs(self, category=None, limit=None):
        """
        获取日志
        
        Args:
            category: 过滤指定类别 (USER_INPUT, AI_REQUEST, AI_RESPONSE, TOOL_CALL, ERRORS)
            limit: 限制返回条数
        """
        result = self._logs
        
        if category:
            result = [log for log in result if log.get('category') == category]
        
        if limit:
            result = result[-limit:]
        
        return result
    
    def clear(self):
        """清空日志"""
        self._logs = []
        self.save()
    
    def get_categories(self):
        """获取所有日志类别"""
        categories = set()
        for log in self._logs:
            categories.add(log.get('category', 'UNKNOWN'))
        return sorted(list(categories))


# 全局日志实例
logger = Logger()

# 确保SYSTEM常量存在
if 'SYSTEM' not in dir():
    SYSTEM = 'SYSTEM'
