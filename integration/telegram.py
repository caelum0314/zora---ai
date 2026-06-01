"""Telegram 集成模块，用于通过 Telegram Bot API 收发消息。"""

# 导入 requests 库，用于发送 HTTP 请求调用 Telegram Bot API
import requests

class Telegram:
    """Telegram Bot 集成客户端，封装消息发送与更新轮询功能。"""

    def __init__(self, bot_token, chat_id):
        # 保存 Telegram Bot 的访问令牌
        self.bot_token = bot_token
        # 保存目标聊天的 ID
        self.chat_id = chat_id
        # 构造 Telegram Bot API 的基础 URL
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        # 记录最后一次处理的 update_id，用于增量拉取
        self.last_update_id = 0

    def send_message(self, content):
        """向预设的 chat_id 发送文本消息。"""
        # 构造 sendMessage API 的完整 URL
        url = f"{self.base_url}/sendMessage"
        # 构造请求参数，包含目标聊天和文本内容
        params = {
            "chat_id": self.chat_id,
            "text": content
        }
        # 发送 GET 请求发送消息
        response = requests.get(url, params=params)
        # 将响应解析为 JSON
        result = response.json()
        # 检查 API 返回的 ok 字段是否为 True
        if result.get("ok"):
            # 返回成功提示
            return "Message sent successfully"
        else:
            # 返回失败信息
            return f"Failed to send message: {result.get('description')}"

    def get_messages(self):
        """获取最新的消息更新，自动维护 update_id 以避免重复拉取。"""
        # 构造 getUpdates API 的完整 URL
        url = f"{self.base_url}/getUpdates"
        # 构造请求参数
        params = {
            # 设置 offset 为上次 update_id + 1，避免拉取已处理的消息
            "offset": self.last_update_id + 1 if self.last_update_id > 0 else 0,
            # 超时时间设为 0，立刻返回已有消息
            "timeout": 0
        }
        # 发送 GET 请求获取消息更新
        response = requests.get(url, params=params)
        # 将响应解析为 JSON
        result = response.json()
        # 检查 API 返回的 ok 字段是否为 True
        if result.get("ok"):
            # 提取更新列表，默认为空列表
            updates = result.get("result", [])
            # 如果有新的更新
            if updates:
                # 更新 last_update_id 为最后一条消息的 update_id
                self.last_update_id = updates[-1].get("update_id", self.last_update_id)
            # 返回更新列表
            return updates
        else:
            # 返回失败信息
            return f"Failed to get messages: {result.get('description')}"