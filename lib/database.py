"""
数据库模块 — 通过 JSON 和 Markdown 文件管理对话上下文与长期记忆。

- context.json：存储当前会话的消息历史（role/content 列表）
- MEMORY.md：持久化存储用户希望 Zora 记住的长期信息
"""
# 导入 JSON 模块，用于序列化和反序列化上下文数据
import json
# 导入 OS 模块，用于文件路径操作和目录创建
import os
# 导入 datetime 模块，用于生成导出文件的时间戳
from datetime import datetime


# 定义 Database 类 — 对话数据持久层
class Database:
    """对话数据持久层，管理上下文（JSON）和长期记忆（Markdown）的读写。"""

    # 初始化方法，设置文件路径并确保文件存在
    def __init__(self, context_file="database/context.json", memory_file="home/MEMORY.md"):
        # 保存上下文 JSON 文件路径
        self.context_file = context_file
        # 保存长期记忆 Markdown 文件路径
        self.memory_file = memory_file
        # 确保数据文件和目录存在
        self._ensure_files()

    # 确保数据文件及其目录存在
    def _ensure_files(self):
        """确保数据文件及其目录存在，不存在则自动创建。"""
        # 如果上下文文件不存在，创建目录和空 JSON 数组文件
        if not os.path.exists(self.context_file):
            # 递归创建父目录（如果不存在）
            os.makedirs(os.path.dirname(self.context_file), exist_ok=True)
            # 打开文件准备写入
            with open(self.context_file, 'w', encoding='utf-8') as f:
                # 写入空列表作为初始上下文
                json.dump([], f)

        # 如果记忆文件不存在，创建目录和初始 Markdown 文件
        if not os.path.exists(self.memory_file):
            # 递归创建父目录（如果不存在）
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            # 打开文件准备写入
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                # 写入 Markdown 标题作为初始内容
                f.write("# Memory\n\n")

    # 读取当前对话上下文
    def get_context(self) -> list:
        """读取当前对话上下文，返回消息列表。"""
        # 尝试打开并读取上下文 JSON 文件
        try:
            # 以只读方式打开上下文文件
            with open(self.context_file, 'r', encoding='utf-8') as f:
                # 从文件中加载 JSON 数据
                data = json.load(f)
                # 如果数据是列表则返回，否则返回空列表
                return data if isinstance(data, list) else []
        # 捕获 JSON 解析错误或文件不存在错误
        except (json.JSONDecodeError, FileNotFoundError):
            # 返回空列表作为默认值
            return []

    # 向上下文追加一条消息
    def add_to_context(self, role: str, content: str):
        """向上下文追加一条消息（role 为 user/assistant/system）。"""
        # 获取当前所有上下文消息
        context = self.get_context()
        # 在消息列表末尾追加新消息
        context.append({"role": role, "content": content})
        # 将更新后的上下文写回文件
        self._write_context(context)

    # 清空全部上下文
    def clear_context(self):
        """清空全部上下文。"""
        # 写入空列表以清空上下文
        self._write_context([])

    # 内部方法：将上下文写入 JSON 文件
    def _write_context(self, context: list):
        """将上下文写入 JSON 文件（内部方法）。"""
        # 以写入方式打开上下文文件
        with open(self.context_file, 'w', encoding='utf-8') as f:
            # 将上下文列表序列化为 JSON 并写入（保留 Unicode，缩进 2 空格）
            json.dump(context, f, ensure_ascii=False, indent=2)

    # 返回上下文消息数量
    def context_size(self) -> int:
        """返回当前上下文中的消息数量。"""
        # 获取上下文并返回其长度
        return len(self.get_context())

    # 读取长期记忆文件内容
    def get_memory(self) -> str:
        """读取长期记忆文件内容。"""
        # 尝试打开并读取记忆文件
        try:
            # 以只读方式打开记忆文件
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                # 返回文件全部内容
                return f.read()
        # 如果文件不存在，返回空字符串
        except FileNotFoundError:
            return ""

    # 向长期记忆追加新内容
    def add_to_memory(self, content: str):
        """向长期记忆文件追加新内容。"""
        # 以追加模式打开记忆文件
        with open(self.memory_file, 'a', encoding='utf-8') as f:
            # 在文件末尾追加内容（前后各加一个换行）
            f.write(f"\n{content}\n")

    # 用摘要替换当前上下文
    def summarize_context(self, summary: str):
        """用摘要替换当前上下文（清空后写入摘要）。"""
        # 先清空所有上下文
        self.clear_context()
        # 将摘要作为 system 消息写入上下文
        self.add_to_context("system", f"Previous conversation summary: {summary}")

    # 导出对话为 Markdown 文件
    def export_markdown(self) -> str:
        """将当前对话导出为带时间戳的 Markdown 文件。"""
        # 获取当前上下文中的所有消息
        context = self.get_context()
        # 生成时间戳字符串（用于文件名）
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        # 构建导出文件名
        filename = f"conversation_{timestamp}.md"

        # 构建 Markdown 文件内容行列表（含标题和导出时间）
        lines = [
            # Markdown 大标题
            f"# Zora Conversation",
            # 导出时间信息
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            # 空行
            "",
            # 分隔线
            "---",
            # 空行
            ""
        ]

        # 遍历每条上下文消息，转换为 Markdown 格式
        for entry in context:
            # 获取消息角色，默认为 "unknown"
            role = entry.get("role", "unknown")
            # 获取消息内容，默认为空字符串
            content = entry.get("content", "")
            # 根据角色设置对应的 Markdown 标题
            if role == "user":
                # 用户消息标题
                lines.append(f"### You")
            elif role == "assistant":
                # AI 助手消息标题
                lines.append(f"### Zora")
            elif role == "system":
                # 系统消息标题
                lines.append(f"### System")
            else:
                # 其他角色直接使用角色名
                lines.append(f"### {role}")
            # 标题后空一行
            lines.append("")
            # 消息正文内容
            lines.append(content)
            # 内容后空一行
            lines.append("")

        # 将行列表用换行符连接为完整文本
        text = "\n".join(lines)
        # 构建输出文件的完整路径
        filepath = os.path.join(os.getcwd(), filename)
        # 以写入方式打开文件
        with open(filepath, 'w', encoding='utf-8') as f:
            # 将 Markdown 文本写入文件
            f.write(text)

        # 返回导出完成的信息
        return f"Conversation exported to {filename} ({len(context)} messages)"
