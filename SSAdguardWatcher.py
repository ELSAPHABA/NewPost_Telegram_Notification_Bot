import re
from decimal import Decimal

from bs4 import BeautifulSoup

from SiteWatcher import SiteWatcher


class SSAdguardWatcher(SiteWatcher):
    PRICE_SELECTOR = (
        "body > div.emo-zf0iqh > main > div.emo-1s9h98g > div.emo-1fmf28w > "
        "div > div.emo-1u67s5k > div.emo-zqska8 > div.emo-1n89a02 > div > "
        "div.emo-1m9ze8p > span.chakra-text.emo-14fwmk1"
    )
    PRICE_PATTERN = re.compile(r"\$?\s*(\d+(?:\.\d+)?)")
    ALERT_THRESHOLD = Decimal("14")

    def __init__(self):
        super().__init__()
        self.name = "StackSocial AdGuard"
        self.url = "https://www.stacksocial.com/sales/adguard-family-plan-lifetime-subscription"
        self._alert_condition_met = False

    def get_latest_post(self, headers=None):
        price_text = self._fetch_price_text(headers=headers)
        price = self._parse_price(price_text)
        post_id = int(price * 100)
        return post_id, price_text, self.url

    def process_scraped_post(self, post_id, title, link):
        price = Decimal(post_id) / 100
        condition_met = price < self.ALERT_THRESHOLD

        if not condition_met:
            self._alert_condition_met = False
            self.last_post_id = None
            return None, None

        if self._alert_condition_met:
            return None, None

        self._alert_condition_met = True
        self.last_post_id = post_id
        return title, link

    async def send_telegram(self, bot, chat_id, text, link):
        await bot.send_message(
            chat_id=chat_id,
            text=f"[{self.name}] {text} 도달\n{link}",
        )

    def _fetch_price_text(self, headers=None):
        html = self.fetch_page(headers=headers)
        soup = BeautifulSoup(html, "html.parser")

        price_element = soup.select_one(self.PRICE_SELECTOR)
        if price_element:
            return price_element.get_text(" ", strip=True)

        for price_candidate in soup.select("span.chakra-text"):
            text = price_candidate.get_text(" ", strip=True)
            if self.PRICE_PATTERN.fullmatch(text):
                return text

        raise Exception(f"{self.name}: 가격 span을 찾을 수 없습니다.")

    def _parse_price(self, price_text):
        match = self.PRICE_PATTERN.search(price_text)
        if not match:
            raise Exception(f'{self.name}: 가격을 찾을 수 없습니다: "{price_text}"')
        return Decimal(match.group(1))
