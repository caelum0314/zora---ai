import requests

class Telegram:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
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