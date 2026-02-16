import requests

class TelegramClient:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send(self, html):
        if not self.token or not self.chat_id:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        requests.get(url, params={
            "chat_id": self.chat_id,
            "text": html,
            "parse_mode": "HTML",
        })
