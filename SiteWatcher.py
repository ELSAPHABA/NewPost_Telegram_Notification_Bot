# SiteWatcher.py

import requests
import time

from config import get_proxy_manager

class SiteWatcher:
    def __init__(self):
        self.name = None
        self.url = None
        self.last_post_id = None
        self.interval = 30
        self.source_load_delay = 1
        self.request_timeout = 5
        self.scrape_retry_timeout = 10
        self.scrape_retry_delay = 1
        self._scrape_deadline = None

    def fetch_response(self, headers=None, timeout=None):
        headers = headers or {'User-Agent': 'Mozilla/5.0'}
        base_timeout = timeout or self.request_timeout

        proxy_manager = get_proxy_manager()
        for attempt in range(proxy_manager.request_attempts()):
            try:
                request_timeout = self._request_timeout(base_timeout)
                response = requests.get(
                    self.url,
                    headers=headers,
                    timeout=request_timeout,
                    proxies=proxy_manager.requests_proxies(),
                )
                response.raise_for_status()
                break
            except requests.RequestException:
                proxy_manager.rotate_now()
                if attempt == proxy_manager.request_attempts() - 1:
                    raise

        if self.source_load_delay > 0:
            delay = self.source_load_delay
            if self._scrape_deadline is not None:
                remaining = self._scrape_deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"{self.name}: 스크래핑 제한 시간을 초과했습니다.")
                delay = min(delay, remaining)
            time.sleep(delay)
        return response

    def _request_timeout(self, timeout):
        if self._scrape_deadline is None:
            return timeout

        remaining = self._scrape_deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"{self.name}: 스크래핑 제한 시간을 초과했습니다.")
        return min(timeout, remaining)

    def fetch_page(self, headers=None):
        response = self.fetch_response(headers=headers)
        return response.text

    def get_latest_post(self, headers=None):
        raise NotImplementedError

    def check_new_post_with_headers(self, headers):
        deadline = time.monotonic() + self.scrape_retry_timeout
        last_error = None
        post_id = title = link = None
        previous_deadline = self._scrape_deadline
        self._scrape_deadline = deadline

        try:
            while time.monotonic() < deadline:
                try:
                    post_id, title, link = self.get_latest_post(headers=headers)
                    break
                except Exception as e:
                    last_error = e
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    time.sleep(min(self.scrape_retry_delay, remaining))
        finally:
            self._scrape_deadline = previous_deadline

        if post_id is None:
            raise TimeoutError(f"{self.name}: 10초 내 스크래핑에 실패했습니다.") from last_error

        if self.last_post_id != post_id:
            self.last_post_id = post_id
            return title, link
        return None, None

    async def send_telegram(self, bot, chat_id, text, link):
        await bot.send_message(chat_id=chat_id, text=f"[{self.name}] 새 글: {text}\n{link}")

