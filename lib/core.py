"""
核心模块 — 负责 AI 对话、命令执行、上下文管理和技能发现。

Core 类是 Zora 的中枢控制器，协调以下子系统：
- OpenAI 客户端：处理与 LLM 的流式对话
- Database：管理对话上下文和长期记忆
- Terminal：安全执行 shell 命令
- 技能发现：扫描 skill/ 目录并生成可用技能目录
"""
# 导入 JSON 模块，用于解析配置文件
import json
# 导入 OS 模块，用于文件系统操作（目录检查、路径处理）
import os
# 导入 subprocess 模块，用于执行外部子进程
import subprocess
# 导入 sys 模块，用于系统相关操作
import sys
# 导入 time 模块，用于延时等待（API 重试退避）
import time
# 导入 OpenAI 客户端，用于与 LLM 进行流式对话
from openai import OpenAI
# 导入数据库模块，管理对话上下文和长期记忆
from lib.database import Database
# 导入终端模块，安全执行 shell 命令
from lib.terminal import Terminal


# 定义 Core 类 — Zora 的核心控制器
class Core:
    """Zora 核心控制器，管理 AI 对话生命周期、命令执行与技能调用。"""

    # 初始化方法，加载配置并创建各子系统实例
    def __init__(self, config_file="config.json"):
        # 打开并读取 JSON 配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            # 将配置文件内容解析为字典，赋值给实例属性
            self.config = json.load(f)

        # 初始化 OpenAI 兼容客户端，使用配置中的 API 密钥和基础 URL
        self.client = OpenAI(
            # 从配置中读取 API 密钥
            api_key=self.config['openai']['api_key'],
            # 从配置中读取 API 基础 URL
            base_url=self.config['openai']['base_url']
        )

        # 创建数据库实例，管理对话上下文和记忆
        self.database = Database()
        # 创建终端实例，安全执行 shell 命令
        self.terminal = Terminal()
        # 设置上下文长度限制，默认 30 条消息
        self.context_limit = self.config.get("context_limit", 30)

    # 扫描 skill/ 目录，构建可用技能目录字符串
    def discover_skills(self) -> str:
        """扫描 skill/ 目录，构建技能目录字符串，用于注入系统提示词。"""
        # 定义技能脚本所在的目录名
        skill_dir = "skill"
        # 如果技能目录不存在，返回空字符串
        if not os.path.isdir(skill_dir):
            return ""

        # 静态技能目录，避免 Windows 下子进程调用问题
        static_catalog = {
            # 扫描源代码结构的技能
            "code_scan.py": "扫描源代码结构 — 类、函数、导入、TODO",
            # 正则搜索代码内容的技能
            "code_search.py": "正则搜索代码内容",
            # 执行命令并诊断错误的技能
            "diagnose.py": "执行命令并诊断错误",
            # 查看 git diff 摘要的技能
            "diff_review.py": "查看 git diff 摘要",
            # 读取文件内容的技能
            "file_read.py": "读取文件内容（带行号）",
            # 跨文件查找替换的技能
            "find_replace.py": "跨文件查找替换",
            # git 操作的技能
            "git_ops.py": "git 状态/日志/分支操作",
            # pip 操作的技能
            "pip_ops.py": "pip 安装/卸载/列表",
            # 运行测试的技能
            "run_test.py": "运行测试",
            # 网络搜索的技能
            "web.py": "网络搜索",
            # 写文件的技能
            "write_file.py": "写文件或追加内容",
        }

        # 初始化技能目录列表
        catalog = []
        # 遍历技能目录中的所有文件（按名称排序）
        for fname in sorted(os.listdir(skill_dir)):
            # 跳过非 Python 文件或以下划线开头的私有文件
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            # 从静态目录中查找描述，若找不到则使用默认描述
            desc = static_catalog.get(fname, "执行技能脚本")
            # 将文件名和描述加入目录列表
            catalog.append(f"  {fname} — {desc}")

        # 如果目录非空，用换行符连接并返回；否则返回空字符串
        return "\n".join(catalog) if catalog else ""

    # 构建发送给 LLM 的完整消息列表
    def _build_messages(self, user_input: str) -> list:
        """构建发送给 LLM 的完整消息列表，包含系统提示词、记忆、上下文和技能目录。"""
        # 获取当前对话上下文（历史消息列表）
        context = self.database.get_context()
        # 获取长期记忆内容
        memory = self.database.get_memory()
        # 获取可用技能目录字符串
        skills_catalog = self.discover_skills()

        # 组装技能提示块（初始为空）
        skill_block = ""
        # 如果技能目录非空，构建完整的技能提示块
        if skills_catalog:
            skill_block = (
                # 技能标题
                "\n## 可用技能\n"
                # 技能使用说明
                "你可以通过 command: 标签调用以下技能脚本（放在回复末尾即可）：\n"
                # 调用语法说明
                "语法: command python skill/<skill_name>.py <args>\n\n"
                # 插入具体的技能目录
                f"{skills_catalog}\n"
                # 使用提示
                "\n使用时请先了解用户需求，选择合适技能，在回复中附上 command: 调用。\n"
            )

        # 从配置中获取基础系统提示词，默认使用通用提示
        base_prompt = self.config.get("system_prompt", "你是 Zora，一个编程助手。")

        # 构建完整的消息列表：系统提示词 + 记忆 + 上下文 + 用户输入
        messages = [
            # 第一个 system 消息：基础提示词拼接技能块
            {"role": "system", "content": base_prompt + skill_block},
            # 第二个 system 消息：注入长期记忆
            {"role": "system", "content": f"Memory: {memory}"}
        ] + context + [
            # 用户当前输入
            {"role": "user", "content": user_input}
        ]
        # 返回构建好的消息列表
        return messages

    # 获取 AI 流式响应，支持自动重试和上下文裁剪
    def get_chat_response(self, user_input: str) -> str:
        """获取 AI 流式响应（实时打印），支持自动重试和上下文自动裁剪。"""
        # 构建发送给 LLM 的消息列表
        messages = self._build_messages(user_input)

        # 发送前自动裁剪过长上下文，避免超出 token 限制
        self._auto_trim()

        # 初始化响应文本为空字符串
        response_text = ""
        # 初始化最后一次错误为 None
        last_error = None

        # 最多重试 3 次，每次失败后带退避等待
        for attempt in range(3):
            # 尝试发送请求并接收流式响应
            try:
                # 调用 OpenAI API，启用流式输出
                stream = self.client.chat.completions.create(
                    # 使用配置中指定的模型
                    model=self.config['openai']['model'],
                    # 传入构建好的消息列表
                    messages=messages,
                    # 启用流式传输
                    stream=True,
                    # 设置请求超时为 60 秒
                    timeout=60
                )

                # 遍历流式响应中的每个数据块
                for chunk in stream:
                    # 检查数据块中是否有有效的文本内容
                    if chunk.choices and chunk.choices[0].delta.content:
                        # 提取当前 token 文本
                        token = chunk.choices[0].delta.content
                        # 实时打印 token 到终端（不换行）
                        print(token, end="", flush=True)
                        # 将 token 追加到响应文本中
                        response_text += token

                # 流式输出结束后输出一个换行符
                print()
                # 成功后跳出重试循环
                break

            # 捕获所有异常
            except Exception as e:
                # 记录最后一次错误
                last_error = e
                # 如果不是最后一次尝试，进行退避重试
                if attempt < 2:
                    # 计算退避等待时间：2秒、4秒
                    wait = (attempt + 1) * 2
                    # 打印重试提示信息
                    print(f"\n[API error, retrying in {wait}s...]", flush=True)
                    # 等待指定秒数
                    time.sleep(wait)
                # 最后一次尝试仍失败，输出错误信息
                else:
                    # 打印最终失败信息
                    print(f"\n[API error after 3 attempts: {last_error}]", flush=True)
                    # 返回错误信息给调用方
                    return f"Error: API call failed — {last_error}"

        # 去除响应文本首尾空白字符
        response_text = response_text.strip()
        # 如果响应为空，返回错误信息
        if not response_text:
            return "Error: empty response from API"

        # 将用户输入存入对话上下文
        self.database.add_to_context("user", user_input)
        # 将 AI 响应存入对话上下文
        self.database.add_to_context("assistant", response_text)

        # 返回完整的 AI 响应文本
        return response_text

    # 上下文过长时自动压缩
    def _auto_trim(self):
        """上下文过长时自动压缩：将前半部分摘要化，保留后半部分。"""
        # 获取当前上下文消息列表
        context = self.database.get_context()
        # 检查上下文是否超出限制
        if len(context) > self.context_limit:
            # 取前半部分作为"旧"上下文，用于生成摘要
            cutoff = len(context) // 2
            # 前半部分（将被摘要化）
            old = context[:cutoff]
            # 后半部分（将被保留）
            new = context[cutoff:]
            # 尝试调用 LLM 生成摘要
            try:
                # 构建摘要请求消息
                summary_msg = [
                    # 系统指令：要求简洁地摘要对话历史
                    {"role": "system", "content": "Summarize this conversation history concisely:"},
                    # 传入需要摘要的旧上下文
                    {"role": "user", "content": str(old)}
                ]
                # 调用 LLM 生成摘要（限制输出 200 token）
                r = self.client.chat.completions.create(
                    # 使用配置中的模型
                    model=self.config['openai']['model'],
                    # 传入摘要请求消息
                    messages=summary_msg,
                    # 限制摘要最大 token 数
                    max_tokens=200
                )
                # 提取生成的摘要文本
                summary = r.choices[0].message.content
                # 清空当前所有上下文
                self.database.clear_context()
                # 将摘要作为 system 消息加入上下文
                self.database.add_to_context("system", f"Previous conversation summary: {summary}")
                # 将后半部分原始消息逐一加回上下文
                for entry in new:
                    self.database.add_to_context(entry["role"], entry["content"])
            # 如果摘要生成失败，静默忽略
            except Exception:
                pass

    # 执行 shell 命令（带安全检查）
    def execute_command(self, command: str) -> str:
        # 调用安全检查，判断命令是否属于危险操作
        if self.terminal.is_dangerous(command):
            # 返回拦截提示，告知用户命令被阻止
            return (
                # 危险命令拦截信息
                f"  Dangerous command blocked: '{command}'\n"
                # 风险说明
                "  This command could cause data loss or system damage.\n"
                # 告知用户如何强制执行的语法
                "  If you're sure, type: command !! {command}"
            )
        # 通过安全检查后，正常执行命令
        return self.terminal.execute(command)

    # 强制执行被拦截的危险命令
    def force_execute(self, command: str) -> str:
        """强制执行被安全检查拦截的命令（用户明确确认后调用）。"""
        # 跳过安全检查，直接执行命令
        return self.terminal.execute(command)

    # 手动触发上下文摘要
    def summarize_context(self):
        """手动触发上下文摘要：将当前对话压缩为一段摘要并替换上下文。"""
        # 获取当前上下文
        context = self.database.get_context()
        # 如果上下文为空，返回提示
        if not context:
            return "No context to summarize."

        # 构建摘要请求消息
        messages = [
            # 系统指令：要求简洁摘要
            {"role": "system", "content": "Summarize the following conversation concisely:"},
            # 传入当前上下文内容
            {"role": "user", "content": str(context)}
        ]

        # 调用 LLM 生成摘要
        response = self.client.chat.completions.create(
            # 使用配置中的模型
            model=self.config['openai']['model'],
            # 传入摘要请求
            messages=messages
        )

        # 提取生成的摘要文本
        summary = response.choices[0].message.content
        # 用摘要替换当前上下文
        self.database.summarize_context(summary)
        # 返回摘要文本
        return summary

    # 清空当前对话上下文
    def clear_context(self):
        """清空当前对话上下文。"""
        # 调用数据库方法清空上下文
        self.database.clear_context()
        # 返回确认信息
        return "Context cleared."

    # 将内容追加到长期记忆
    def add_to_memory(self, content):
        """将内容追加到长期记忆文件。"""
        # 调用数据库方法追加记忆
        self.database.add_to_memory(content)
        # 返回确认信息
        return "Added to memory."

    # 导出对话为 Markdown 文件
    def export_conversation(self) -> str:
        """将当前对话导出为 Markdown 文件。"""
        # 调用数据库方法导出对话
        return self.database.export_markdown()
