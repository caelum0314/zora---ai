import json
import os
import subprocess
import sys
import time
from openai import OpenAI
from lib.database import Database
from lib.terminal import Terminal


class Core:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.client = OpenAI(
            api_key=self.config['openai']['api_key'],
            base_url=self.config['openai']['base_url']
        )

        self.database = Database()
        self.terminal = Terminal()
        self.context_limit = self.config.get("context_limit", 30)

    def discover_skills(self) -> str:
        """Scan skill/ directory and build a catalog string for the system prompt."""
        skill_dir = "skill"
        if not os.path.isdir(skill_dir):
            return ""

        # Static skill catalog to avoid subprocess issues on Windows
        static_catalog = {
            "code_scan.py": "扫描源代码结构 — 类、函数、导入、TODO",
            "code_search.py": "正则搜索代码内容",
            "diagnose.py": "执行命令并诊断错误",
            "diff_review.py": "查看 git diff 摘要",
            "file_read.py": "读取文件内容（带行号）",
            "find_replace.py": "跨文件查找替换",
            "git_ops.py": "git 状态/日志/分支操作",
            "pip_ops.py": "pip 安装/卸载/列表",
            "run_test.py": "运行测试",
            "web.py": "网络搜索",
            "write_file.py": "写文件或追加内容",
        }

        catalog = []
        for fname in sorted(os.listdir(skill_dir)):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            desc = static_catalog.get(fname, "执行技能脚本")
            catalog.append(f"  {fname} — {desc}")

        return "\n".join(catalog) if catalog else ""

    def _build_messages(self, user_input: str) -> list:
        context = self.database.get_context()
        memory = self.database.get_memory()
        skills_catalog = self.discover_skills()

        skill_block = ""
        if skills_catalog:
            skill_block = (
                "\n## 可用技能\n"
                "你可以通过 command: 标签调用以下技能脚本（放在回复末尾即可）：\n"
                "语法: command python skill/<skill_name>.py <args>\n\n"
                f"{skills_catalog}\n"
                "\n使用时请先了解用户需求，选择合适技能，在回复中附上 command: 调用。\n"
            )

        base_prompt = self.config.get("system_prompt", "你是 Zora，一个编程助手。")

        messages = [
            {"role": "system", "content": base_prompt + skill_block},
            {"role": "system", "content": f"Memory: {memory}"}
        ] + context + [
            {"role": "user", "content": user_input}
        ]
        return messages

    def get_chat_response(self, user_input: str) -> str:
        """Get AI response with streaming (printed in real-time), retry, and auto-trim."""
        messages = self._build_messages(user_input)

        # Auto-trim context before sending if too large
        self._auto_trim()

        response_text = ""
        last_error = None

        for attempt in range(3):
            try:
                stream = self.client.chat.completions.create(
                    model=self.config['openai']['model'],
                    messages=messages,
                    stream=True,
                    timeout=60
                )

                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        print(token, end="", flush=True)
                        response_text += token

                print()  # newline after streaming
                break

            except Exception as e:
                last_error = e
                if attempt < 2:
                    wait = (attempt + 1) * 2
                    print(f"\n[API error, retrying in {wait}s...]", flush=True)
                    time.sleep(wait)
                else:
                    print(f"\n[API error after 3 attempts: {last_error}]", flush=True)
                    return f"Error: API call failed — {last_error}"

        response_text = response_text.strip()
        if not response_text:
            return "Error: empty response from API"

        self.database.add_to_context("user", user_input)
        self.database.add_to_context("assistant", response_text)

        return response_text

    def _auto_trim(self):
        """If context is too long, automatically summarize old entries."""
        context = self.database.get_context()
        if len(context) > self.context_limit:
            # Summarize oldest half
            cutoff = len(context) // 2
            old = context[:cutoff]
            new = context[cutoff:]
            try:
                summary_msg = [
                    {"role": "system", "content": "Summarize this conversation history concisely:"},
                    {"role": "user", "content": str(old)}
                ]
                r = self.client.chat.completions.create(
                    model=self.config['openai']['model'],
                    messages=summary_msg,
                    max_tokens=200
                )
                summary = r.choices[0].message.content
                self.database.clear_context()
                self.database.add_to_context("system", f"Previous conversation summary: {summary}")
                for entry in new:
                    self.database.add_to_context(entry["role"], entry["content"])
            except Exception:
                pass

    def execute_command(self, command: str) -> str:
        # Safety check
        if self.terminal.is_dangerous(command):
            return (
                f"  Dangerous command blocked: '{command}'\n"
                "  This command could cause data loss or system damage.\n"
                "  If you're sure, type: command !! {command}"
            )
        return self.terminal.execute(command)

    def force_execute(self, command: str) -> str:
        """Execute a command that was blocked by the safety filter."""
        return self.terminal.execute(command)

    def summarize_context(self):
        context = self.database.get_context()
        if not context:
            return "No context to summarize."

        messages = [
            {"role": "system", "content": "Summarize the following conversation concisely:"},
            {"role": "user", "content": str(context)}
        ]

        response = self.client.chat.completions.create(
            model=self.config['openai']['model'],
            messages=messages
        )

        summary = response.choices[0].message.content
        self.database.summarize_context(summary)
        return summary

    def clear_context(self):
        self.database.clear_context()
        return "Context cleared."

    def add_to_memory(self, content):
        self.database.add_to_memory(content)
        return "Added to memory."

    def export_conversation(self) -> str:
        return self.database.export_markdown()
