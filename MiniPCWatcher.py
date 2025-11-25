# MiniPCWatcher.py

from bs4 import BeautifulSoup
from SiteWatcher import SiteWatcher

class MiniPCWatcher(SiteWatcher):
    def __init__(self):
        super().__init__()
        self.name = "MiniPC"
        self.url = "https://gall.dcinside.com/mgallery/board/lists/?id=minipc&sort_type=N&search_head=20&page=1"

    def get_latest_post(self, headers=None):
        html = self.fetch_page(headers=headers)
        soup = BeautifulSoup(html, 'html.parser')
        # 광고/공지를 건너뛰고 실제 게시글(us-post) 중 첫 번째를 선택
        tr = soup.select_one('.gall_listwrap.list table tbody tr.us-post')
        if not tr:
            raise Exception('MiniPC: 새글 tr을 찾을 수 없습니다.')
        post_id = tr.get('data-no')
        a_tag = tr.select_one('td.gall_tit.ub-word > a')
        if not a_tag:
            raise Exception('MiniPC: 제목 링크를 찾을 수 없습니다.')
        title = a_tag.get_text(strip=True)
        href = a_tag.get('href')
        if href.startswith('/'):
            link = 'https://gall.dcinside.com' + href
        else:
            link = href
        return int(post_id), title, link