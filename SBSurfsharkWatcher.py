import re
from decimal import Decimal

from bs4 import BeautifulSoup

from SiteWatcher import SiteWatcher


class SBSurfsharkWatcher(SiteWatcher):
    CASHBACK_SELECTOR = (
        r"body > div.d_flex.flex_column.min-h_100dvh > main > div > "
        r"div.d_flex.items_center.gap_10px.flex_column.w_100\%.lg\:max-w_1352."
        r"px_sbds-dimension-space-size-m.md\:px_sbds-dimension-size-13."
        r"sm\:flex_row.gap-y_sbds-dimension-space-size-xl.md\:gap-y_0."
        r"gap-x_sbds-dimension-space-size-xl.lg\:gap-x_sbds-dimension-size-15-5."
        r"flex-wrap_wrap.items_flex-start.transform_translateY\(-63px\) > "
        r"div.d_flex.w_100\%.flex_1_0_min-content.flex_column."
        r"gap_sbds-dimension-space-size-xl.lg\:gap_sbds-dimension-size-15-5 > "
        r"div.d_flex.flex_column.gap_0.overflow_hidden > "
        r"div.d_flex.flex_column.items_stretch.flex-wrap_wrap."
        r"gap_sbds-dimension-space-size-s.w_100\%.pos_relative > div > div > h2"
    )
    CASHBACK_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*캐시백")
    ALERT_THRESHOLD = Decimal("95")

    def __init__(self):
        super().__init__()
        self.name = "ShopBack Surfshark"
        self.url = "https://www.shopback.co.kr/surfshark-vpn"
        self._alert_condition_met = False

    def get_latest_post(self, headers=None):
        cashback_text = self._fetch_cashback_text(headers=headers)
        cashback_percent = self._parse_cashback_percent(cashback_text)
        post_id = int(cashback_percent * 100)
        return post_id, cashback_text, self.url

    def check_new_post_with_headers(self, headers):
        post_id, title, link = self.get_latest_post(headers=headers)
        cashback_percent = Decimal(post_id) / 100
        condition_met = cashback_percent >= self.ALERT_THRESHOLD

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

    def _fetch_cashback_text(self, headers=None):
        html = self.fetch_page(headers=headers)
        soup = BeautifulSoup(html, "html.parser")

        cashback_element = soup.select_one(self.CASHBACK_SELECTOR)
        if cashback_element:
            return cashback_element.get_text(" ", strip=True)

        for heading in soup.select("h2"):
            text = heading.get_text(" ", strip=True)
            if self.CASHBACK_PATTERN.search(text):
                return text

        raise Exception(f"{self.name}: 캐시백 h2를 찾을 수 없습니다.")

    def _parse_cashback_percent(self, cashback_text):
        match = self.CASHBACK_PATTERN.search(cashback_text)
        if not match:
            raise Exception(f'{self.name}: 캐시백 퍼센트를 찾을 수 없습니다: "{cashback_text}"')
        return Decimal(match.group(1))
