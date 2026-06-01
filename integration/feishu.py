"""飞书（Lark）集成模块，用于通过飞书开放平台 API 收发消息。"""

import json
import requests


class Feishu:
    """飞书集成客户端，封装 app_access_token 认证、消息发送与接收功能。"""

    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None

    def get_access_token(self):
        """获取 app_access_token，用于后续 API 调用的认证。"""
        url = f"{self.base_url}/auth/v3/app_access_token/internal/"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            self.access_token = result.get("app_access_token")
            return self.access_token
        else:
            raise Exception(f"Failed to get access token: {result.get('msg')}")

    def send_message(self, chat_id, content):
        """向指定群聊发送文本消息。token 过期时会自动重新获取。"""
        if not self.access_token:
            self.get_access_token()

        url = f"{self.base_url}/im/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        data = {
            "receive_id_type": "chat_id",
            "receive_id": chat_id,
            "content": json.dumps({"text": content}),
            "msg_type": "text"
        }
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return "Message sent successfully"
        else:
            return f"Failed to send message: {result.get('msg')}"

    def get_messages(self, chat_id, limit=10):
        """获取指定群聊的历史消息列表。不包含已撤回的消息。"""
        if not self.access_token:
            self.get_access_token()

        url = f"{self.base_url}/im/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        params = {
            "chat_id": chat_id,
            "limit": limit,
            "reverse": False
        }
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        if result.get("code") == 0:
            return result.get("data", {}).get("items", [])
        else:
            return f"Failed to get messages: {result.get('msg')}"