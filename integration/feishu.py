"""飞书（Lark）集成模块，用于通过飞书开放平台 API 收发消息。"""

# 导入 json 模块，用于构造 API 请求中的 JSON 内容
import json
# 导入 requests 库，用于发送 HTTP 请求调用飞书 API
import requests


class Feishu:
    """飞书集成客户端，封装 app_access_token 认证、消息发送与接收功能。"""

    def __init__(self, app_id, app_secret):
        # 保存飞书应用的 App ID
        self.app_id = app_id
        # 保存飞书应用的 App Secret
        self.app_secret = app_secret
        # 飞书开放平台 API 的基础 URL
        self.base_url = "https://open.feishu.cn/open-apis"
        # 初始化 access_token 为空，后续按需获取
        self.access_token = None

    def get_access_token(self):
        """获取 app_access_token，用于后续 API 调用的认证。"""
        # 构造获取 token 的请求 URL
        url = f"{self.base_url}/auth/v3/app_access_token/internal/"
        # 设置请求头，指定内容类型为 JSON
        headers = {"Content-Type": "application/json"}
        # 构造请求体，包含 app_id 和 app_secret
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        # 发送 POST 请求获取 access_token
        response = requests.post(url, headers=headers, json=data)
        # 将响应解析为 JSON 对象
        result = response.json()
        # 检查 API 返回码是否为 0（表示成功）
        if result.get("code") == 0:
            # 从响应中提取 app_access_token 并保存
            self.access_token = result.get("app_access_token")
            # 返回获取到的 access_token
            return self.access_token
        else:
            # 获取失败时抛出异常
            raise Exception(f"Failed to get access token: {result.get('msg')}")

    def send_message(self, chat_id, content):
        """向指定群聊发送文本消息。token 过期时会自动重新获取。"""
        # 如果 access_token 为空，先获取 token
        if not self.access_token:
            self.get_access_token()

        # 构造发送消息的 API URL
        url = f"{self.base_url}/im/v1/messages"
        # 设置请求头，包含认证 token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        # 构造消息请求体
        data = {
            # 指定接收者为群聊
            "receive_id_type": "chat_id",
            # 目标群聊 ID
            "receive_id": chat_id,
            # 消息内容，JSON 格式的文本
            "content": json.dumps({"text": content}),
            # 消息类型为文本
            "msg_type": "text"
        }
        # 发送 POST 请求发送消息
        response = requests.post(url, headers=headers, json=data)
        # 将响应解析为 JSON
        result = response.json()
        # 检查返回码是否为 0（成功）
        if result.get("code") == 0:
            # 返回成功提示
            return "Message sent successfully"
        else:
            # 返回失败信息
            return f"Failed to send message: {result.get('msg')}"

    def get_messages(self, chat_id, limit=10):
        """获取指定群聊的历史消息列表。不包含已撤回的消息。"""
        # 如果 access_token 为空，先获取 token
        if not self.access_token:
            self.get_access_token()

        # 构造获取消息列表的 API URL
        url = f"{self.base_url}/im/v1/messages"
        # 设置请求头，包含认证 token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        # 构造查询参数
        params = {
            # 指定群聊 ID
            "chat_id": chat_id,
            # 返回消息的数量上限
            "limit": limit,
            # 不反转消息顺序
            "reverse": False
        }
        # 发送 GET 请求获取消息列表
        response = requests.get(url, headers=headers, params=params)
        # 将响应解析为 JSON
        result = response.json()
        # 检查返回码是否为 0（成功）
        if result.get("code") == 0:
            # 返回消息列表，默认为空列表
            return result.get("data", {}).get("items", [])
        else:
            # 返回失败信息
            return f"Failed to get messages: {result.get('msg')}"