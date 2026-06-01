"""Zora AI 主入口模块，提供 CLI 交互循环，处理用户命令和 AI 对话。"""

# 导入 json 模块，用于解析 API 返回的 JSON 数据
import json
# 导入 os 模块，用于文件路径操作
import os
# 导入 threading 模块，用于后台线程轮询消息
import threading
# 导入 time 模块，用于线程休眠控制轮询间隔
import time
# 导入 rich 库的 Console，用于终端彩色输出
from rich.console import Console
# 导入 rich 库的 Markdown，用于渲染 Markdown 格式文本
from rich.markdown import Markdown
# 导入 rich 库的 Live，用于动态刷新终端内容
from rich.live import Live
# 导入 rich 库的 Spinner，用于显示加载旋转动画
from rich.spinner import Spinner
# 导入核心模块，提供 AI 对话和命令执行功能
from lib.core import Core
# 导入飞书集成模块
from integration.feishu import Feishu
# 导入 Telegram 集成模块
from integration.telegram import Telegram




class Main:
    """主控制器，管理 CLI 交互循环、飞书/Telegram 消息轮询和 AI 对话。"""

    def __init__(self):
        # 初始化 rich Console 实例，用于终端彩色输出
        self.console = Console()
        # 初始化 AI 核心模块
        self.core = Core()

        # 打开并读取配置文件 config.json
        with open('config.json', 'r', encoding='utf-8') as f:
            # 将 JSON 配置解析为 Python 字典
            config = json.load(f)

        # 初始化飞书客户端为 None（默认不启用）
        self.feishu = None
        # 从配置中提取飞书相关设置
        feishu_config = config.get('feishu', {})
        # 检查飞书 app_id 和 app_secret 是否都已配置
        if feishu_config.get('app_id') and feishu_config.get('app_secret'):
            # 排除占位符值（以 'your_' 开头），确保是真实配置
            if not feishu_config['app_id'].startswith('your_'):
                # 使用真实配置初始化飞书客户端
                self.feishu = Feishu(feishu_config['app_id'], feishu_config['app_secret'])

        # 初始化 Telegram 客户端为 None（默认不启用）
        self.telegram = None
        # 从配置中提取 Telegram 相关设置
        telegram_config = config.get('telegram', {})
        # 检查 Telegram bot_token 和 chat_id 是否都已配置
        if telegram_config.get('bot_token') and telegram_config.get('chat_id'):
            # 排除占位符值（以 'your_' 开头），确保是真实配置
            if not telegram_config['bot_token'].startswith('your_'):
                # 使用真实配置初始化 Telegram 客户端
                self.telegram = Telegram(telegram_config['bot_token'], telegram_config['chat_id'])

        # 设置程序运行状态标志
        self.running = True

        # 创建后台守护线程，用于轮询飞书和 Telegram 消息
        self.message_thread = threading.Thread(target=self.check_messages, daemon=True)
        # 启动后台消息轮询线程
        self.message_thread.start()

        # 显示欢迎界面
        self._show_welcome()

    def _show_welcome(self):
        """显示欢迎界面、内置命令和可用技能的帮助信息。"""
        # 定义 ASCII 艺术字欢迎标语
        welcome_art = """
   _____ _           _        _ _           _   _
  / ____| |         | |      | | |         | | (_)
 | |    | |__   ___ | |_ __ _| | | ___  ___| |_ _  ___  _ __
 | |    | '_ \\ / _ \\| __/ _` | | |/ _ \\/ __| __| |/ _ \\| '_ \\
 | |____| | | | (_) | || (_| | | |  __/\\__ \\ |_| | (_) | | | |
  \\_____|_| |_|\\___/ \\__\\__,_|_|_|\\___||___/\\__|_|\\___/|_| |_|


"""
        # 以青色输出欢迎标语
        self.console.print(welcome_art, style="cyan")
        # 以绿色粗体输出程序名称
        self.console.print("Zora AI  — 终端编程助手\n", style="green bold")
        # 输出内置命令标题
        self.console.print("内置命令:")
        # 输出各内置命令及对应功能说明
        self.console.print("  summary    压缩上下文    clear     清空历史")
        # 输出导出和退出命令
        self.console.print("  export     导出对话      exit      退出")
        # 输出 Shell 命令模式说明
        self.console.print("  command    Shell命令     !!        强制执行(跳过安全检查)")
        # 输出飞书和 Telegram 消息命令
        self.console.print("  feishu     飞书消息      telegram  Telegram消息")
        # 输出空行分隔
        self.console.print("")
        # 以暗色输出编程技能标题
        self.console.print("编程技能 (AI 自动调用):", style="dim")
        # 以暗色输出第一行可用的编程技能
        self.console.print("  code_search  find_replace  code_scan  file_read  write_file", style="dim")
        # 以暗色输出第二行可用的编程技能
        self.console.print("  git_ops      diff_review   run_test   diagnose   pip_ops", style="dim")
        # 输出空行分隔
        self.console.print("")

    def _spin(self, message: str):
        """显示加载动画，提示 AI 正在思考中。"""
        # 返回一个旋转动画状态显示对象
        return self.console.status(f"[bold green]{message}[/bold green]", spinner="dots")

    def check_messages(self):
        """后台线程：每隔 5 秒轮询飞书和 Telegram 的新消息。
        支持 command: 前缀（执行命令）和 ai: 前缀（AI 对话）。"""
        # 当程序处于运行状态时持续轮询
        while self.running:
            # 如果飞书客户端已初始化
            if self.feishu:
                try:
                    # 从核心配置中获取飞书 chat_id
                    chat_id = self.core.config.get('feishu', {}).get('chat_id', '')
                    # 检查 chat_id 是否有效且非占位符
                    if chat_id and not chat_id.startswith('your_'):
                        # 获取最近的飞书消息（最多 5 条）
                        messages = self.feishu.get_messages(chat_id, limit=5)
                        # 确认返回的是消息列表
                        if isinstance(messages, list):
                            # 遍历每条消息
                            for msg in messages:
                                # 提取消息内容，默认为空 JSON
                                content = msg.get('content', '{}')
                                try:
                                    # 将消息内容字符串解析为 JSON 对象
                                    content_json = json.loads(content)
                                    # 提取文本内容并去除首尾空白
                                    text = content_json.get('text', '').strip()
                                    # 如果文本以 'command:' 开头，表示这是一条命令
                                    if text.startswith('command:'):
                                        # 提取命令文本
                                        command = text[8:].strip()
                                        # 在终端输出收到的飞书命令
                                        self.console.print(f"[feishu] 命令: {command}", style="cyan")
                                        # 执行该命令并获取结果
                                        result = self.core.execute_command(command)
                                        # 在终端输出命令执行结果
                                        self.console.print(result, style="blue")
                                        # 将执行结果通过飞书发送回去
                                        self.feishu.send_message(chat_id, f"result:\n{result}")
                                    # 如果文本以 'ai:' 开头，表示这是一个 AI 提问
                                    elif text.startswith('ai:'):
                                        # 提取 AI 提问内容
                                        question = text[3:].strip()
                                        # 在终端输出收到的飞书 AI 提问
                                        self.console.print(f"[feishu] AI: {question}", style="cyan")
                                        # 调用 AI 获取对话回复
                                        response = self.core.get_chat_response(question)
                                        # 将 AI 回复通过飞书发送回去
                                        self.feishu.send_message(chat_id, f"{response}")
                                # 忽略 JSON 解析错误的消息
                                except json.JSONDecodeError:
                                    pass
                # 捕获飞书轮询中的异常并在终端显示
                except Exception as e:
                    # 以红色在终端输出飞书相关错误
                    self.console.print(f"[feishu] error: {e}", style="red")

            # 如果 Telegram 客户端已初始化
            if self.telegram:
                try:
                    # 获取 Telegram 消息更新列表
                    updates = self.telegram.get_messages()
                    # 确认返回的是更新列表
                    if isinstance(updates, list):
                        # 遍历每条更新
                        for update in updates:
                            # 提取消息对象，默认为空字典
                            message = update.get('message', {})
                            # 提取消息文本并去除首尾空白
                            text = message.get('text', '').strip()
                            # 获取消息来源的聊天 ID
                            chat_id = message.get('chat', {}).get('id', self.telegram.chat_id)
                            # 如果文本以 'command:' 开头，表示这是一条命令
                            if text.startswith('command:'):
                                # 提取命令文本
                                command = text[8:].strip()
                                # 在终端输出收到的 Telegram 命令
                                self.console.print(f"[tg] 命令: {command}", style="cyan")
                                # 执行该命令并获取结果
                                result = self.core.execute_command(command)
                                # 在终端输出命令执行结果
                                self.console.print(result, style="blue")
                                # 将执行结果通过 Telegram 发送回去
                                self.telegram.send_message(f"result:\n{result}")
                            # 如果文本以 'ai:' 开头，表示这是一个 AI 提问
                            elif text.startswith('ai:'):
                                # 提取 AI 提问内容
                                question = text[3:].strip()
                                # 在终端输出收到的 Telegram AI 提问
                                self.console.print(f"[tg] AI: {question}", style="cyan")
                                # 调用 AI 获取对话回复
                                response = self.core.get_chat_response(question)
                                # 将 AI 回复通过 Telegram 发送回去
                                self.telegram.send_message(f"{response}")
                # 捕获 Telegram 轮询中的异常并在终端显示
                except Exception as e:
                    # 以红色在终端输出 Telegram 相关错误
                    self.console.print(f"[tg] error: {e}", style="red")

            # 每次轮询后休眠 5 秒，避免频繁请求
            time.sleep(5)

    def run(self):
        """CLI 主循环，处理用户输入的各种命令。"""
        # 无限循环等待用户输入
        while True:
            try:
                # 读取用户输入并去除首尾空白
                user_input = input(">> ").strip()
                # 如果输入为空，跳过进入下一轮循环
                if not user_input:
                    continue

                # 如果输入 "exit"，退出程序
                if user_input == "exit":
                    # 设置运行状态为 False，停止后台线程
                    self.running = False
                    # 输出再见信息
                    self.console.print("Bye!", style="green")
                    # 跳出主循环
                    break

                # 如果输入 "summary"，压缩对话上下文
                elif user_input == "summary":
                    # 调用核心模块汇总精简上下文
                    result = self.core.summarize_context()
                    # 以黄色输出汇总结果
                    self.console.print(result, style="yellow")

                # 如果输入 "clear"，清空对话历史
                elif user_input == "clear":
                    # 调用核心模块清空上下文
                    result = self.core.clear_context()
                    # 以黄色输出清空结果
                    self.console.print(result, style="yellow")

                # 如果输入 "export"，导出对话记录
                elif user_input == "export":
                    # 调用核心模块导出对话
                    result = self.core.export_conversation()
                    # 以绿色输出导出结果
                    self.console.print(result, style="green")

                # 如果输入以 "!! " 开头，强制执行命令（跳过安全检查）
                elif user_input.startswith("!! "):
                    # 提取 "!! " 之后的命令文本
                    command = user_input[3:]
                    # 调用核心模块强制执行命令
                    result = self.core.force_execute(command)
                    # 以黄色输出执行结果
                    self.console.print(result, style="yellow")

                # 如果输入以 "command " 开头，安全执行 Shell 命令
                elif user_input.startswith("command "):
                    # 提取 "command " 之后的命令文本
                    command = user_input[8:]
                    # 调用核心模块安全执行命令
                    result = self.core.execute_command(command)
                    # 以蓝色输出执行结果
                    self.console.print(result, style="blue")

                # 如果输入以 "feishu " 开头，通过飞书发送消息
                elif user_input.startswith("feishu "):
                    # 检查飞书客户端是否已初始化
                    if self.feishu:
                        # 提取 "feishu " 之后的消息文本
                        message = user_input[7:]
                        # 通过飞书发送消息并获取结果
                        result = self.feishu.send_message(
                            self.core.config['feishu'].get('chat_id', ''), message)
                        # 以蓝色输出发送结果
                        self.console.print(result, style="blue")
                    # 飞书客户端未配置
                    else:
                        # 以红色提示飞书未配置
                        self.console.print("feishu not configured", style="red")

                # 如果输入以 "telegram " 开头，通过 Telegram 发送消息
                elif user_input.startswith("telegram "):
                    # 检查 Telegram 客户端是否已初始化
                    if self.telegram:
                        # 提取 "telegram " 之后的消息文本
                        message = user_input[9:]
                        # 通过 Telegram 发送消息并获取结果
                        result = self.telegram.send_message(message)
                        # 以蓝色输出发送结果
                        self.console.print(result, style="blue")
                    # Telegram 客户端未配置
                    else:
                        # 以红色提示 Telegram 未配置
                        self.console.print("telegram not configured", style="red")

                # 其他输入视为 AI 对话
                else:
                    # 调用核心模块获取 AI 对话回复
                    response = self.core.get_chat_response(user_input)

                    # 尝试从 AI 响应中提取可执行命令
                    if "command:" in response:
                        # 提取 "command:" 之后的文本作为命令
                        command = response.split("command:")[-1].strip()
                    elif "\ncommand " in response:
                        # 提取换行后 "command " 之后的文本作为命令
                        command = response.split("\ncommand ")[-1].strip()
                    elif response.startswith("command "):
                        # 提取以 "command " 开头的响应中的命令
                        command = response[8:].strip()
                    else:
                        # AI 响应中不含命令
                        command = ""
                    # 如果提取到了有效命令
                    if command:
                        # 执行该命令
                        result = self.core.execute_command(command)
                        # 以蓝色输出执行结果
                        self.console.print(f"\n{result}", style="blue")

            # 捕获 Ctrl+C 中断
            except KeyboardInterrupt:
                # 设置运行状态为 False
                self.running = False
                # 输出再见信息
                self.console.print("\nBye!", style="green")
                # 跳出主循环
                break
            # 捕获其他所有异常，保持程序不崩溃
            except Exception as e:
                # 以红色在终端输出错误信息
                self.console.print(f"Error: {e}", style="red")


# 当本文件作为脚本直接运行时
if __name__ == "__main__":
    # 创建 Main 类实例
    app = Main()
    # 启动 CLI 主循环
    app.run()
