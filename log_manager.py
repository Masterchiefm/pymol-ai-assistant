"""
日志管理模块

记录和显示操作日志，包括：
- AI 对话记录
- 工具调用记录
- 系统日志
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# 日志目录
LOG_DIR = Path.home() / ".pymol_ai_assistant" / "logs"
MAX_LOG_ENTRIES = 10000  # 最大日志条目数


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogType(Enum):
    """日志类型"""
    SYSTEM = "system"      # 系统日志
    CHAT = "chat"          # AI 对话
    TOOL_CALL = "tool_call" # 工具调用
    TOOL_RESULT = "tool_result" # 工具结果
    THINKING = "thinking"  # AI 思考过程
    RESPONSE = "response"  # AI 回复


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: float
    level: str
    type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "level": self.level,
            "type": self.type,
            "message": self.message,
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEntry":
        return cls(
            timestamp=data.get("timestamp", time.time()),
            level=data.get("level", LogLevel.INFO.value),
            type=data.get("type", LogType.SYSTEM.value),
            message=data.get("message", ""),
            details=data.get("details")
        )
    
    def format_display(self) -> str:
        """格式化为显示字符串"""
        dt = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")
        return f"[{dt}] [{self.level}] [{self.type}] {self.message}"


class LogManager:
    """
    日志管理器
    
    负责：
    - 记录各类日志
    - 保存日志到文件
    - 提供日志查询和过滤
    - 回调通知（用于实时更新 UI）
    """
    
    def __init__(self):
        self.entries: List[LogEntry] = []
        self.callbacks: List[callable] = []
        self._ensure_log_dir()
        self.session_start = time.time()
        self.current_log_file = LOG_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    def add_callback(self, callback: callable):
        """添加日志更新回调"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: callable):
        """移除日志更新回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, entry: LogEntry):
        """通知所有回调"""
        for callback in self.callbacks:
            try:
                callback(entry)
            except Exception as e:
                print(f"[LogManager] 回调执行失败: {e}")
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO, 
            log_type: LogType = LogType.SYSTEM, details: Optional[Dict[str, Any]] = None):
        """添加日志条目"""
        entry = LogEntry(
            timestamp=time.time(),
            level=level.value,
            type=log_type.value,
            message=message,
            details=details
        )
        
        self.entries.append(entry)
        
        # 限制日志数量
        if len(self.entries) > MAX_LOG_ENTRIES:
            self.entries = self.entries[-MAX_LOG_ENTRIES:]
        
        # 保存到文件
        self._append_to_file(entry)
        
        # 通知回调
        self._notify_callbacks(entry)
        
        return entry
    
    def debug(self, message: str, log_type: LogType = LogType.SYSTEM, details: Optional[Dict[str, Any]] = None):
        """记录调试日志"""
        return self.log(message, LogLevel.DEBUG, log_type, details)
    
    def info(self, message: str, log_type: LogType = LogType.SYSTEM, details: Optional[Dict[str, Any]] = None):
        """记录信息日志"""
        return self.log(message, LogLevel.INFO, log_type, details)
    
    def warning(self, message: str, log_type: LogType = LogType.SYSTEM, details: Optional[Dict[str, Any]] = None):
        """记录警告日志"""
        return self.log(message, LogLevel.WARNING, log_type, details)
    
    def error(self, message: str, log_type: LogType = LogType.SYSTEM, details: Optional[Dict[str, Any]] = None):
        """记录错误日志"""
        return self.log(message, LogLevel.ERROR, log_type, details)
    
    def chat_user(self, message: str):
        """记录用户消息"""
        return self.log(message, LogLevel.INFO, LogType.CHAT, {"role": "user"})
    
    def chat_assistant(self, message: str):
        """记录助手消息"""
        return self.log(message, LogLevel.INFO, LogType.CHAT, {"role": "assistant"})
    
    def thinking(self, message: str):
        """记录 AI 思考过程"""
        return self.log(message, LogLevel.INFO, LogType.THINKING)
    
    def tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """记录工具调用"""
        return self.log(
            f"调用: {tool_name}",
            LogLevel.INFO,
            LogType.TOOL_CALL,
            {"tool_name": tool_name, "arguments": arguments}
        )
    
    def tool_result(self, tool_name: str, result: Dict[str, Any]):
        """记录工具结果"""
        success = result.get("success", False)
        message = result.get("message", "")
        status = "成功" if success else "失败"
        return self.log(
            f"结果: {tool_name} - {status}: {message}",
            LogLevel.INFO,
            LogType.TOOL_RESULT,
            {"tool_name": tool_name, "result": result}
        )
    
    def _append_to_file(self, entry: LogEntry):
        """追加日志到文件"""
        try:
            with open(self.current_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[LogManager] 写入日志文件失败: {e}")
    
    def get_entries(self, log_type: Optional[LogType] = None, 
                    level: Optional[LogLevel] = None,
                    limit: int = 100) -> List[LogEntry]:
        """获取日志条目，支持过滤"""
        entries = self.entries
        
        if log_type:
            entries = [e for e in entries if e.type == log_type.value]
        
        if level:
            level_priority = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARNING: 2, LogLevel.ERROR: 3}
            min_priority = level_priority.get(level, 0)
            entries = [e for e in entries if level_priority.get(LogLevel(e.level), 0) >= min_priority]
        
        return entries[-limit:]
    
    def get_all_entries(self) -> List[LogEntry]:
        """获取所有日志条目"""
        return self.entries.copy()
    
    def clear(self):
        """清空当前会话日志"""
        self.entries.clear()
        self.info("日志已清空")
    
    def get_log_files(self) -> List[Path]:
        """获取所有日志文件"""
        if LOG_DIR.exists():
            return sorted(LOG_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        return []
    
    def load_log_file(self, filepath: Path) -> List[LogEntry]:
        """加载日志文件"""
        entries = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            entries.append(LogEntry.from_dict(data))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[LogManager] 加载日志文件失败: {e}")
        return entries


# 全局日志管理器实例
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """获取全局日志管理器实例"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager
