"""
核心模块 — 负责 AI 对话、命令执行、上下文管理和技能发现。

Core 类是 Zora 的中枢控制器，协调以下子系统：
- OpenAI 客户端：处理与 LLM 的流式对话
- Database：管理对话上下文和长期记忆
- Terminal：安全执行 shell 命令
- 技能发现：扫描 skill/ 目录并生成可用技能目录
"""
import json
import os
import subprocess
import sys
import time
from openai import OpenAI
from lib.database import Database
from lib.terminal import Terminal


class Core:
    """Zora 核心控制器，管理 AI 对话生命周期、命令执行与技能调用。"""

    def __init__(self, config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化 OpenAI 兼容客户端
        self.client = OpenAI(
            api_key=self.config['openai']['api_key'],
            base_url=self.config['openai']['base_url']
        )

        self.database = Database()
        self.terminal = Terminal()
        self.context_limit = self.config.get("context_limit", 30)

    def discover_skills(self) -> str:
        """扫描 skill/ 目录，构建技能目录字符串，用于注入系统提示词。"""
        skill_dir = "skill"
        if not os.path.isdir(skill_dir):
            return ""

        # 静态技能目录，避免 Windows 下子进程调用问题
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
        """构建发送给 LLM 的完整消息列表，包含系统提示词、记忆、上下文和技能目录。"""
        context = self.database.get_context()
        memory = self.database.get_memory()
        skills_catalog = self.discover_skills()

        # 组装技能提示块
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
        """获取 AI 流式响应（实时打印），支持自动重试和上下文自动裁剪。"""
        messages = self._build_messages(user_input)

        # 发送前自动裁剪过长上下文
        self._auto_trim()

        response_text = ""
        last_error = None

        # 最多重试 3 次，带退避等待
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

                print()  # 流式输出结束后换行
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

        # 将本轮对话存入上下文
        self.database.add_to_context("user", user_input)
        self.database.add_to_context("assistant", response_text)

        return response_text

    def _auto_trim(self):
        """上下文过长时自动压缩：将前半部分摘要化，保留后半部分。"""
        context = self.database.get_context()
        if len(context) > self.context_limit:
            # 取前半部分做摘要
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
        # 安全检查：拦截危险命令
        if self.terminal.is_dangerous(command):
            return (
                f"  Dangerous command blocked: '{command}'\n"
                "  This command could cause data loss or system damage.\n"
                "  If you're sure, type: command !! {command}"
            )
        return self.terminal.execute(command)

    def force_execute(self, command: str) -> str:
        """强制执行被安全检查拦截的命令（用户明确确认后调用）。"""
        return self.terminal.execute(command)

    def summarize_context(self):
        """手动触发上下文摘要：将当前对话压缩为一段摘要并替换上下文。"""
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
        """清空当前对话上下文。"""
        self.database.clear_context()
        return "Context cleared."

    def add_to_memory(self, content):
        """将内容追加到长期记忆文件。"""
        self.database.add_to_memory(content)
        return "Added to memory."

    def export_conversation(self) -> str:
        """将当前对话导出为 Markdown 文件。"""
        return self.database.export_markdown()
