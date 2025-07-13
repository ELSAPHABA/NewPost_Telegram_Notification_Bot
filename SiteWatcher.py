# SiteWatcher.py

import requests

class SiteWatcher:
    def __init__(self):
        self.name = None
        self.url = None
        self.last_post_id = None
        self.interval = 30

    def fetch_page(self, headers=None):
        headers = headers or {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_latest_post(self, headers=None):
        raise NotImplementedError

    def check_new_post_with_headers(self, headers):
        post_id, title, link = self.get_latest_post(headers=headers)
        if self.last_post_id != post_id:
            self.last_post_id = post_id
            return title, link
        return None, None

    def send_telegram(self, bot, chat_id, text, link):
        bot.send_message(chat_id=chat_id, text=f"[{self.name}] 새 글: {text}\n{link}")
