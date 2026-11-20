# -*- coding: utf-8 -*-
"""
本地技能（Skill）管理模块

支持从本地文件或文件夹导入 Skill：
- 提示词类 Skill（.md / .txt）：内容注入系统提示词，AI 对话时自动遵循
- 脚本类 Skill（.py / .pml / .pym）：登记路径，AI 通过 pymol_run_script 按需执行

Skill 列表持久化保存在插件配置文件（ConfigManager）中，重启后自动加载。
"""

import os
from typing import Dict, List, Optional

from . import logger

# 提示词类 Skill 支持的扩展名
PROMPT_EXTENSIONS = (".md", ".markdown", ".txt")
# 脚本类 Skill 支持的扩展名
SCRIPT_EXTENSIONS = (".py", ".pym", ".pml")
# 单个 Skill 内容注入系统提示词的最大字符数
MAX_SKILL_CONTENT_CHARS = 20000


class SkillManager:
    """本地技能管理器"""

    def __init__(self):
        self._skills = {}  # {path: {"name":..., "type":..., "enabled":...}}
        self._active_paths = set()  # 当前调用的技能路径（双击激活，运行时状态，不持久化）
        self._loaded = False

    # ---------- 配置读写 ----------

    def load_from_config(self, force=False):
        """从配置文件恢复技能列表（进程内仅加载一次，避免覆盖运行时状态）"""
        if self._loaded and not force:
            return
        from . import config

        saved = config.config_manager.get_skills()
        self._skills = {}
        for item in saved:
            path = self._norm(item.get("path", ""))
            if not path:
                continue
            # 文件可能已被移动或删除，仍保留条目但加载内容时给出提示
            self._skills[path] = {
                "name": item.get("name", os.path.basename(path)),
                "type": item.get("type", "prompt"),
                "enabled": item.get("enabled", True),
            }
        # 清理已失效的激活项
        self._active_paths &= set(self._skills.keys())
        self._loaded = True

    def _save_to_config(self):
        from . import config

        skill_list = [
            {
                "path": path,
                "name": info.get("name", ""),
                "type": info.get("type", "prompt"),
                "enabled": info.get("enabled", True),
            }
            for path, info in self._skills.items()
        ]
        config.config_manager.set_skills(skill_list)

    # ---------- 导入 ----------

    def import_path(self, path: str) -> Dict[str, object]:
        """
        导入文件或文件夹

        Returns:
            {"success": bool, "added": int, "skipped": int, "message": str}
        """
        if not path or not os.path.exists(path):
            return {"success": False, "added": 0, "skipped": 0,
                    "message": "路径不存在: {}".format(path)}

        added, skipped = 0, 0
        if os.path.isfile(path):
            added, skipped = self._import_single_file(path)
        else:
            # 文件夹：遍历（不递归子目录），逐个导入支持的文件类型
            for entry in sorted(os.listdir(path)):
                full = os.path.join(path, entry)
                if os.path.isfile(full) and self._is_supported(full):
                    a, s = self._import_single_file(full)
                    added += a
                    skipped += s
        self._normalize_paths()

        if added > 0:
            self._save_to_config()
            logger.logger.info(logger.SYSTEM, "导入技能成功",
                               {"path": path, "added": added, "skipped": skipped})

        return {
            "success": added > 0,
            "added": added,
            "skipped": skipped,
            "message": "成功导入 {} 个技能，跳过 {} 个（重复或不支持）".format(added, skipped),
        }

    def _import_single_file(self, path: str) -> (int, int):
        """导入单个文件，返回 (added, skipped)"""
        if not self._is_supported(path):
            return 0, 1
        if path in self._skills:
            return 0, 1  # 已导入过，跳过（保持最小作用域，不自动去重更新）
        skill_type = "script" if path.lower().endswith(SCRIPT_EXTENSIONS) else "prompt"
        self._skills[path] = {
            "name": os.path.splitext(os.path.basename(path))[0],
            "type": skill_type,
            "enabled": True,
        }
        return 1, 0

    @staticmethod
    def _is_supported(path: str) -> bool:
        lower = path.lower()
        return lower.endswith(PROMPT_EXTENSIONS) or lower.endswith(SCRIPT_EXTENSIONS)

    @staticmethod
    def _norm(path: str) -> str:
        """路径归一化（统一分隔符与绝对路径，避免 Windows 下 \\ 与 / 不一致）"""
        if not path:
            return ""
        try:
            return os.path.normcase(os.path.abspath(path))
        except Exception:
            return os.path.normpath(path)

    def _normalize_paths(self):
        """将内部存储的所有路径键归一化"""
        for old_path in list(self._skills.keys()):
            new_path = self._norm(old_path)
            if new_path != old_path:
                self._skills[new_path] = self._skills.pop(old_path)
                if old_path in self._active_paths:
                    self._active_paths.discard(old_path)
                    self._active_paths.add(new_path)

    # ---------- 列表操作 ----------

    def get_skills(self) -> List[Dict[str, object]]:
        """获取技能列表 [{path, name, type, enabled}]"""
        result = []
        for path, info in self._skills.items():
            item = dict(info)
            item["path"] = path
            item["exists"] = os.path.exists(path)
            result.append(item)
        return result

    def remove_skill(self, path: str) -> bool:
        path = self._norm(path)
        if path in self._skills:
            del self._skills[path]
            self._active_paths.discard(path)
            self._save_to_config()
            return True
        return False

    def set_enabled(self, path: str, enabled: bool):
        path = self._norm(path)
        if path in self._skills:
            self._skills[path]["enabled"] = enabled
            self._save_to_config()

    # ---------- 当前调用（运行时激活） ----------

    def set_active(self, path: str, active: bool):
        """设置技能的当前调用状态（仅运行时，不写入配置文件）"""
        path = self._norm(path)
        if path in self._skills:
            if active:
                self._active_paths.add(path)
            else:
                self._active_paths.discard(path)

    def is_active(self, path: str) -> bool:
        return self._norm(path) in self._active_paths

    def get_active_skills(self) -> List[str]:
        """获取当前调用的技能路径列表"""
        return [p for p in self._skills if p in self._active_paths]

    # ---------- 系统提示词注入 ----------

    def get_skills_prompt_block(self) -> str:
        """
        生成注入系统提示词的文本块（仅包含当前调用的技能）

        - prompt 类 Skill：读取文件内容直接注入
        - script 类 Skill：登记路径，提示 AI 可用 pymol_run_script 调用
        """
        if not self._active_paths:
            return ""

        prompt_parts = []
        script_parts = []
        for path in sorted(self._active_paths):
            info = self._skills.get(path)
            if not info or not info.get("enabled", True):
                continue
            name = info.get("name", os.path.basename(path))
            if not os.path.exists(path):
                prompt_parts.append("### {}（文件缺失：{}）".format(name, path))
                continue

            if info.get("type") == "script":
                script_parts.append("- {}: {}".format(name, path))
            else:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    prompt_parts.append("### {}（读取失败: {}）".format(name, e))
                    continue
                if len(content) > MAX_SKILL_CONTENT_CHARS:
                    content = content[:MAX_SKILL_CONTENT_CHARS] + "\n...[内容过长已截断]"
                prompt_parts.append("### {}\n{}".format(name, content))

        if not prompt_parts and not script_parts:
            return ""

        lines = ["", "", "【当前调用的本地技能】", "以下技能由用户在本次对话中主动调用，请在对话中遵循其中的指令与约定："]
        lines.extend(prompt_parts)
        if script_parts:
            lines.append("### 可用本地脚本")
            lines.append("用户提供了以下本地脚本，需要时可用 pymol_run_script 工具执行：")
            lines.extend(script_parts)
        return "\n".join(lines)


# 模块级单例
skill_manager = SkillManager()
