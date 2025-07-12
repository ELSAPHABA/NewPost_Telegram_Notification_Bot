import requests
from bs4 import BeautifulSoup

class SiteWatcher:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.last_post_id = None

    def fetch_page(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_latest_post(self):
        """Override this method for each site."""
        raise NotImplementedError

    def check_new_post(self):
        post_id, title, link = self.get_latest_post()
        if self.last_post_id != post_id:
            self.last_post_id = post_id
            return title, link
        return None, None

    def send_telegram(self, text, link):
        """텔레그램 봇 전송용 틀 함수 (API 구현 필요)"""
        print(f"[{self.name}] 새 글 알림: {text}\n{link}")
        # 실제로는 requests.post로 텔레그램 API 호출
        pass


class DCGalleryWatcher(SiteWatcher):
    def get_latest_post(self):
        html = self.fetch_page()
        soup = BeautifulSoup(html, 'html.parser')
        # tr:nth-child(3): 실제 새글 위치, 고정글/공지글 있을 수 있으니 필요시 조정
        tr = soup.select_one(
            '#container > section.left_content > article:nth-child(3) > div.gall_listwrap.list > table > tbody > tr:nth-child(3)'
        )
        if not tr:
            raise Exception('새글 tr을 찾을 수 없습니다.')

        post_id = tr.get('data-no')
        # 제목/링크
        a_tag = tr.select_one('td.gall_tit.ub-word > a')
        if not a_tag:
            raise Exception('제목 링크를 찾을 수 없습니다.')
        title = a_tag.get_text(strip=True)
        href = a_tag.get('href')
        if href.startswith('/'):
            link = 'https://gall.dcinside.com' + href
        else:
            link = href

        return int(post_id), title, link


# 예시 사용법
if __name__ == "__main__":
    watcher = DCGalleryWatcher(
        name="미니PC갤",
        url="https://gall.dcinside.com/mgallery/board/lists/?id=minipc&sort_type=N&search_head=20&page=1"
    )
    
    # 초기 상태에서 한 번 실행 (보통 저장된 last_post_id와 비교)
    title, link = watcher.check_new_post()
    if title:
        watcher.send_telegram(title, link)
    else:
        print("새 글이 없습니다.")

    # 반복 실행시 watcher.last_post_id가 갱신됨