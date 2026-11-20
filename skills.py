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

    # ---------- 配置读写 ----------

    def load_from_config(self):
        """从配置文件恢复技能列表"""
        from . import config

        saved = config.config_manager.get_skills()
        self._skills = {}
        for item in saved:
            path = item.get("path", "")
            if not path:
                continue
            # 文件可能已被移动或删除，仍保留条目但加载内容时给出提示
            self._skills[path] = {
                "name": item.get("name", os.path.basename(path)),
                "type": item.get("type", "prompt"),
                "enabled": item.get("enabled", True),
            }

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
        if path in self._skills:
            del self._skills[path]
            self._save_to_config()
            return True
        return False

    def set_enabled(self, path: str, enabled: bool):
        if path in self._skills:
            self._skills[path]["enabled"] = enabled
            self._save_to_config()

    # ---------- 系统提示词注入 ----------

    def get_skills_prompt_block(self) -> str:
        """
        生成注入系统提示词的文本块

        - prompt 类 Skill：读取文件内容直接注入
        - script 类 Skill：登记路径，提示 AI 可用 pymol_run_script 调用
        """
        if not self._skills:
            return ""

        prompt_parts = []
        script_parts = []
        for path, info in sorted(self._skills.items()):
            if not info.get("enabled", True):
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

        lines = ["", "", "【已加载的本地技能】", "以下技能由用户导入，请在对话中遵循其中的指令与约定："]
        lines.extend(prompt_parts)
        if script_parts:
            lines.append("### 可用本地脚本")
            lines.append("用户提供了以下本地脚本，需要时可用 pymol_run_script 工具执行：")
            lines.extend(script_parts)
        return "\n".join(lines)


# 模块级单例
skill_manager = SkillManager()
