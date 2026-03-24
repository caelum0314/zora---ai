import requests

class Telegram:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
    
    def send_message(self, content):
        url = f"{self.base_url}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": content
        }
        response = requests.get(url, params=params)
        result = response.json()
        if result.get("ok"):
            return "Message sent successfully"
        else:
            return f"Failed to send message: {result.get('description')}"
    
    def get_messages(self):
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1 if self.last_update_id > 0 else 0,
            "timeout": 0
        }
        response = requests.get(url, params=params)
        result = response.json()
        if result.get("ok"):
            updates = result.get("result", [])
            if updates:
                self.last_update_id = updates[-1].get("update_id", self.last_update_id)
            return updates
        else:
            return f"Failed to get messages: {result.get('description')}"