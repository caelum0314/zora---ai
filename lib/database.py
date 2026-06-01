"""
数据库模块 — 通过 JSON 和 Markdown 文件管理对话上下文与长期记忆。

- context.json：存储当前会话的消息历史（role/content 列表）
- MEMORY.md：持久化存储用户希望 Zora 记住的长期信息
"""
import json
import os
from datetime import datetime


class Database:
    """对话数据持久层，管理上下文（JSON）和长期记忆（Markdown）的读写。"""

    def __init__(self, context_file="database/context.json", memory_file="home/MEMORY.md"):
        self.context_file = context_file
        self.memory_file = memory_file
        self._ensure_files()

    def _ensure_files(self):
        """确保数据文件及其目录存在，不存在则自动创建。"""
        if not os.path.exists(self.context_file):
            os.makedirs(os.path.dirname(self.context_file), exist_ok=True)
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

        if not os.path.exists(self.memory_file):
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write("# Memory\n\n")

    def get_context(self) -> list:
        """读取当前对话上下文，返回消息列表。"""
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def add_to_context(self, role: str, content: str):
        """向上下文追加一条消息（role 为 user/assistant/system）。"""
        context = self.get_context()
        context.append({"role": role, "content": content})
        self._write_context(context)

    def clear_context(self):
        """清空全部上下文。"""
        self._write_context([])

    def _write_context(self, context: list):
        """将上下文写入 JSON 文件（内部方法）。"""
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)

    def context_size(self) -> int:
        """返回当前上下文中的消息数量。"""
        return len(self.get_context())

    def get_memory(self) -> str:
        """读取长期记忆文件内容。"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def add_to_memory(self, content: str):
        """向长期记忆文件追加新内容。"""
        with open(self.memory_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{content}\n")

    def summarize_context(self, summary: str):
        """用摘要替换当前上下文（清空后写入摘要）。"""
        self.clear_context()
        self.add_to_context("system", f"Previous conversation summary: {summary}")

    def export_markdown(self) -> str:
        """将当前对话导出为带时间戳的 Markdown 文件。"""
        context = self.get_context()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"conversation_{timestamp}.md"

        lines = [
            f"# Zora Conversation",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]

        for entry in context:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            # 根据角色设置对应的标题
            if role == "user":
                lines.append(f"### You")
            elif role == "assistant":
                lines.append(f"### Zora")
            elif role == "system":
                lines.append(f"### System")
            else:
                lines.append(f"### {role}")
            lines.append("")
            lines.append(content)
            lines.append("")

        text = "\n".join(lines)
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

        return f"Conversation exported to {filename} ({len(context)} messages)"
