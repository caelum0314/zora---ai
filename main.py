import json
import os
from rich.console import Console
from rich.markdown import Markdown
from lib.core import Core
from integration.feishu import Feishu
from integration.telegram import Telegram

class Main:
    def __init__(self):
        self.console = Console()
        self.core = Core()
        
        # 加载配置
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 初始化集成
        self.feishu = None
        if config['feishu']['app_id'] and config['feishu']['app_secret']:
            self.feishu = Feishu(config['feishu']['app_id'], config['feishu']['app_secret'])
        
        self.telegram = None
        if config['telegram']['bot_token'] and config['telegram']['chat_id']:
            self.telegram = Telegram(config['telegram']['bot_token'], config['telegram']['chat_id'])
        
        self._show_welcome()
    
    def _show_welcome(self):
        welcome_art = """
   _____ _           _        _ _           _   _              
  / ____| |         | |      | | |         | | (_)             
 | |    | |__   ___ | |_ __ _| | | ___  ___| |_ _  ___  _ __  
 | |    | '_ \ / _ \| __/ _` | | |/ _ \/ __| __| |/ _ \| '_ \ 
 | |____| | | | (_) | || (_| | | |  __/\__ \ |_| | (_) | | | |
  \_____|_| |_|\___/ \__\__,_|_|_|\___||___/\__|_|\___/|_| |_|
                                                              
                                                              
"""
        self.console.print(welcome_art, style="cyan")
        self.console.print("欢迎使用 Zora AI 助手！\n", style="green")
        self.console.print("可用命令:")
        self.console.print("  summary - 压缩当前上下文")
        self.console.print("  clear - 清空所有上下文历史")
        self.console.print("  command <命令> - 执行Shell命令")
        self.console.print("  feishu <消息> - 发送消息到飞书")
        self.console.print("  telegram <消息> - 发送消息到Telegram")
        self.console.print("  exit - 退出程序\n")
    
    def run(self):
        while True:
            try:
                user_input = input(">> ").strip()
                if not user_input:
                    continue
                
                if user_input == "exit":
                    self.console.print("再见！", style="green")
                    break
                elif user_input == "summary":
                    result = self.core.summarize_context()
                    self.console.print(result, style="yellow")
                elif user_input == "clear":
                    result = self.core.clear_context()
                    self.console.print(result, style="yellow")
                elif user_input.startswith("command "):
                    command = user_input[8:]
                    result = self.core.execute_command(command)
                    self.console.print(result, style="blue")
                elif user_input.startswith("feishu "):
                    if self.feishu:
                        message = user_input[7:]
                        result = self.feishu.send_message(self.core.config['feishu'].get('chat_id', ''), message)
                        self.console.print(result, style="blue")
                    else:
                        self.console.print("飞书未配置", style="red")
                elif user_input.startswith("telegram "):
                    if self.telegram:
                        message = user_input[9:]
                        result = self.telegram.send_message(message)
                        self.console.print(result, style="blue")
                    else:
                        self.console.print("Telegram未配置", style="red")
                else:
                    # 处理AI对话
                    response = self.core.get_chat_response(user_input)
                    # 检查是否包含command:标签
                    if "command:" in response:
                        command = response.split("command:")[-1].strip()
                        result = self.core.execute_command(command)
                        self.console.print(Markdown(response), style="green")
                        self.console.print(result, style="blue")
                    else:
                        self.console.print(Markdown(response), style="green")
            except KeyboardInterrupt:
                self.console.print("\n再见！", style="green")
                break
            except Exception as e:
                self.console.print(f"错误: {str(e)}", style="red")

if __name__ == "__main__":
    app = Main()
    app.run()