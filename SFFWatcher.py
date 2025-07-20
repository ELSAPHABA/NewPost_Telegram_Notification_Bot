# SFFWatcher.py

from bs4 import BeautifulSoup
from SiteWatcher import SiteWatcher

class SFFWatcher(SiteWatcher):
    def __init__(self):
        super().__init__()
        self.name = "SFF"
        self.url = "https://gall.dcinside.com/mgallery/board/lists/?id=sff&sort_type=N&search_head=100&page=1"

    def get_latest_post(self, headers=None):
        html = self.fetch_page(headers=headers)
        soup = BeautifulSoup(html, 'html.parser')
        tr = soup.select_one(
            '#container > section.left_content > article:nth-child(3) > div.gall_listwrap.list > table > tbody > tr:nth-child(3)'
        )
        if not tr:
            raise Exception('SFF: 새글 tr을 찾을 수 없습니다.')
        post_id = tr.get('data-no')
        a_tag = tr.select_one('td.gall_tit.ub-word > a')
        if not a_tag:
            raise Exception('SFF: 제목 링크를 찾을 수 없습니다.')
        title = a_tag.get_text(strip=True)
        href = a_tag.get('href')
        if href.startswith('/'):
            link = 'https://gall.dcinside.com' + href
        else:
            link = href
        return int(post_id), title, link