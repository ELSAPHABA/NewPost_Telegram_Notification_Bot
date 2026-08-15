# SiteWatcher.py

import logging
import requests
import time

from config import get_proxy_manager

DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Sec-Ch-Ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}

class SiteWatcher:
    def __init__(self):
        self.name = None
        self.url = None
        self.last_post_id = None
        self.interval = 30
        self.source_load_delay = 1
        self.request_timeout = 5
        self.scrape_retry_timeout = 30
        self.scrape_retry_delay = 1
        self._scrape_deadline = None

    def fetch_response(self, headers=None, timeout=None):
        request_headers = DEFAULT_HEADERS.copy()
        if self.url:
            request_headers['Referer'] = self.url
        if headers:
            request_headers.update(headers)
        request_timeout = timeout or self.request_timeout
        if self._scrape_deadline is not None:
            remaining = self._scrape_deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"{self.name}: 스크래핑 제한 시간을 초과했습니다.")
            request_timeout = min(request_timeout, remaining)

        response = requests.get(
            self.url,
            headers=request_headers,
            timeout=request_timeout,
            proxies=get_proxy_manager().requests_proxies(),
        )
        response.raise_for_status()
        if self.source_load_delay > 0:
            delay = self.source_load_delay
            if self._scrape_deadline is not None:
                remaining = self._scrape_deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"{self.name}: 스크래핑 제한 시간을 초과했습니다.")
                delay = min(delay, remaining)
            time.sleep(delay)
        return response

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
                    logging.warning(f"[{self.name}] 스크래핑 시도 실패: {type(e).__name__}: {e}")
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    time.sleep(min(self.scrape_retry_delay, remaining))
        finally:
            self._scrape_deadline = previous_deadline

        if post_id is None:
            cause_str = f" (원인: {type(last_error).__name__}: {last_error})" if last_error else ""
            raise TimeoutError(f"{self.name}: {self.scrape_retry_timeout}초 내 스크래핑에 실패했습니다.{cause_str}") from last_error

        if self.last_post_id != post_id:
            self.last_post_id = post_id
            return title, link
        return None, None

    async def send_telegram(self, bot, chat_id, text, link):
        await bot.send_message(chat_id=chat_id, text=f"[{self.name}] 새 글: {text}\n{link}")

