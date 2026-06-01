"""Zora AI 主入口模块，提供 CLI 交互循环，处理用户命令和 AI 对话。"""

import json
import os
import sys
import threading
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from lib.core import Core
from integration.feishu import Feishu
from integration.telegram import Telegram

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "memory"))
from save_chat import save_conversation


class Main:
    """主控制器，管理 CLI 交互循环、飞书/Telegram 消息轮询和 AI 对话。"""

    def __init__(self):
        self.console = Console()
        self.core = Core()

        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 初始化飞书集成（仅当配置了有效的 app_id 时）
        self.feishu = None
        feishu_config = config.get('feishu', {})
        if feishu_config.get('app_id') and feishu_config.get('app_secret'):
            if not feishu_config['app_id'].startswith('your_'):
                self.feishu = Feishu(feishu_config['app_id'], feishu_config['app_secret'])

        # 初始化 Telegram 集成（仅当配置了有效的 bot_token 时）
        self.telegram = None
        telegram_config = config.get('telegram', {})
        if telegram_config.get('bot_token') and telegram_config.get('chat_id'):
            if not telegram_config['bot_token'].startswith('your_'):
                self.telegram = Telegram(telegram_config['bot_token'], telegram_config['chat_id'])

        self.running = True

        # 启动后台线程，轮询飞书和 Telegram 的新消息
        self.message_thread = threading.Thread(target=self.check_messages, daemon=True)
        self.message_thread.start()

        self._show_welcome()

    def _show_welcome(self):
        """显示欢迎界面、内置命令和可用技能的帮助信息。"""
        welcome_art = """
   _____ _           _        _ _           _   _
  / ____| |         | |      | | |         | | (_)
 | |    | |__   ___ | |_ __ _| | | ___  ___| |_ _  ___  _ __
 | |    | '_ \\ / _ \\| __/ _` | | |/ _ \\/ __| __| |/ _ \\| '_ \\
 | |____| | | | (_) | || (_| | | |  __/\\__ \\ |_| | (_) | | | |
  \\_____|_| |_|\\___/ \\__\\__,_|_|_|\\___||___/\\__|_|\\___/|_| |_|


"""
        self.console.print(welcome_art, style="cyan")
        self.console.print("Zora AI  — 终端编程助手\n", style="green bold")
        self.console.print("内置命令:")
        self.console.print("  summary    压缩上下文    clear     清空历史")
        self.console.print("  export     导出对话      exit      退出")
        self.console.print("  command    Shell命令     !!        强制执行(跳过安全检查)")
        self.console.print("  feishu     飞书消息      telegram  Telegram消息")
        self.console.print("")
        self.console.print("编程技能 (AI 自动调用):", style="dim")
        self.console.print("  code_search  find_replace  code_scan  file_read  write_file", style="dim")
        self.console.print("  git_ops      diff_review   run_test   diagnose   pip_ops", style="dim")
        self.console.print("")

    def _spin(self, message: str):
        """显示加载动画，提示 AI 正在思考中。"""
        return self.console.status(f"[bold green]{message}[/bold green]", spinner="dots")

    def check_messages(self):
        """后台线程：每隔 5 秒轮询飞书和 Telegram 的新消息。
        支持 command: 前缀（执行命令）和 ai: 前缀（AI 对话）。"""
        while self.running:
            if self.feishu:
                try:
                    chat_id = self.core.config.get('feishu', {}).get('chat_id', '')
                    if chat_id and not chat_id.startswith('your_'):
                        messages = self.feishu.get_messages(chat_id, limit=5)
                        if isinstance(messages, list):
                            for msg in messages:
                                content = msg.get('content', '{}')
                                try:
                                    content_json = json.loads(content)
                                    text = content_json.get('text', '').strip()
                                    if text.startswith('command:'):
                                        command = text[8:].strip()
                                        self.console.print(f"[feishu] 命令: {command}", style="cyan")
                                        result = self.core.execute_command(command)
                                        self.console.print(result, style="blue")
                                        self.feishu.send_message(chat_id, f"result:\n{result}")
                                    elif text.startswith('ai:'):
                                        question = text[3:].strip()
                                        self.console.print(f"[feishu] AI: {question}", style="cyan")
                                        response = self.core.get_chat_response(question)
                                        self.feishu.send_message(chat_id, f"{response}")
                                except json.JSONDecodeError:
                                    pass
                except Exception as e:
                    self.console.print(f"[feishu] error: {e}", style="red")

            if self.telegram:
                try:
                    updates = self.telegram.get_messages()
                    if isinstance(updates, list):
                        for update in updates:
                            message = update.get('message', {})
                            text = message.get('text', '').strip()
                            chat_id = message.get('chat', {}).get('id', self.telegram.chat_id)
                            if text.startswith('command:'):
                                command = text[8:].strip()
                                self.console.print(f"[tg] 命令: {command}", style="cyan")
                                result = self.core.execute_command(command)
                                self.console.print(result, style="blue")
                                self.telegram.send_message(f"result:\n{result}")
                            elif text.startswith('ai:'):
                                question = text[3:].strip()
                                self.console.print(f"[tg] AI: {question}", style="cyan")
                                response = self.core.get_chat_response(question)
                                self.telegram.send_message(f"{response}")
                except Exception as e:
                    self.console.print(f"[tg] error: {e}", style="red")

            time.sleep(5)

    def run(self):
        """CLI 主循环，处理用户输入的各种命令。"""
        while True:
            try:
                user_input = input(">> ").strip()
                if not user_input:
                    continue

                if user_input == "exit":
                    self.running = False
                    self.console.print("Bye!", style="green")
                    break

                # 压缩对话上下文，减少 token 消耗
                elif user_input == "summary":
                    result = self.core.summarize_context()
                    self.console.print(result, style="yellow")

                elif user_input == "clear":
                    result = self.core.clear_context()
                    self.console.print(result, style="yellow")

                elif user_input == "export":
                    result = self.core.export_conversation()
                    self.console.print(result, style="green")

                # !! 前缀：强制执行命令，跳过安全检查
                elif user_input.startswith("!! "):
                    command = user_input[3:]
                    result = self.core.force_execute(command)
                    self.console.print(result, style="yellow")

                # command 前缀：安全执行 Shell 命令
                elif user_input.startswith("command "):
                    command = user_input[8:]
                    result = self.core.execute_command(command)
                    self.console.print(result, style="blue")

                # 通过飞书发送消息
                elif user_input.startswith("feishu "):
                    if self.feishu:
                        message = user_input[7:]
                        result = self.feishu.send_message(
                            self.core.config['feishu'].get('chat_id', ''), message)
                        self.console.print(result, style="blue")
                    else:
                        self.console.print("feishu not configured", style="red")

                # 通过 Telegram 发送消息
                elif user_input.startswith("telegram "):
                    if self.telegram:
                        message = user_input[9:]
                        result = self.telegram.send_message(message)
                        self.console.print(result, style="blue")
                    else:
                        self.console.print("telegram not configured", style="red")

                else:
                    # AI 对话：响应由 core 实时流式输出
                    response = self.core.get_chat_response(user_input)

                    # 自动保存对话记录到本地
                    try:
                        save_conversation(user_input, response)
                    except Exception:
                        pass

                    # 检查 AI 响应中是否包含需要执行的命令
                    if "command:" in response:
                        command = response.split("command:")[-1].strip()
                    elif "\ncommand " in response:
                        command = response.split("\ncommand ")[-1].strip()
                    elif response.startswith("command "):
                        command = response[8:].strip()
                    else:
                        command = ""
                    if command:
                        result = self.core.execute_command(command)
                        self.console.print(f"\n{result}", style="blue")

            except KeyboardInterrupt:
                self.running = False
                self.console.print("\nBye!", style="green")
                break
            except Exception as e:
                # 捕获其他异常，保持程序继续运行
                self.console.print(f"Error: {e}", style="red")


if __name__ == "__main__":
    app = Main()
    app.run()
