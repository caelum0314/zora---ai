import json
import os
from datetime import datetime


class Database:
    def __init__(self, context_file="database/context.json", memory_file="home/MEMORY.md"):
        self.context_file = context_file
        self.memory_file = memory_file
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(self.context_file):
            os.makedirs(os.path.dirname(self.context_file), exist_ok=True)
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

        if not os.path.exists(self.memory_file):
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write("# Memory\n\n")

    def get_context(self) -> list:
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def add_to_context(self, role: str, content: str):
        context = self.get_context()
        context.append({"role": role, "content": content})
        self._write_context(context)

    def clear_context(self):
        self._write_context([])

    def _write_context(self, context: list):
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)

    def context_size(self) -> int:
        return len(self.get_context())

    def get_memory(self) -> str:
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def add_to_memory(self, content: str):
        with open(self.memory_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{content}\n")

    def summarize_context(self, summary: str):
        self.clear_context()
        self.add_to_context("system", f"Previous conversation summary: {summary}")

    def export_markdown(self) -> str:
        """Export current conversation as a Markdown file."""
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
