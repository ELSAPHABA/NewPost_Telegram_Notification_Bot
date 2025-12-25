# TwoCPUWatcher.py

from bs4 import BeautifulSoup
from SiteWatcher import SiteWatcher
from urllib.parse import urljoin
import requests

class TwoCPUWatcher(SiteWatcher):
    def __init__(self):
        """
        TwoCPUWatcher 클래스의 생성자입니다.
        감시할 사이트의 이름과 URL을 설정합니다.
        """
        super().__init__()
        self.name = "2CPU"
        self.url = "https://www.2cpu.co.kr/ha"

    def fetch_page(self, headers=None):
        """
        requests를 사용하여 웹 페이지의 HTML을 가져옵니다.
        2cpu 사이트의 EUC-KR 인코딩에 맞게 처리하도록 부모 클래스의 메서드를 오버라이드합니다.
        """
        headers = headers or {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        # EUC-KR로 인코딩을 명시적으로 설정합니다.
        response.encoding = 'euc-kr'
        return response.text

    def get_latest_post(self, headers=None):
        html = self.fetch_page(headers=headers)
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.select_one('#list_ha table')
        if not table:
            raise Exception('2CPU: table을 찾지 못했습니다.')

        # tbody가 없어도 되도록
        trs = table.find_all('tr', recursive=False)

        latest_post_tr = None
        for tr in trs:
            classes = tr.get('class')
            if not classes or (('is_notice' not in classes) and ('visible-xs' not in classes)):
                latest_post_tr = tr
                break

        if not latest_post_tr:
            raise Exception('2CPU: 최신 게시글 행(tr)을 찾을 수 없습니다.')

        # 첫번째 td(hidden-xs)의 span에서 글번호 추출
        post_id_element = latest_post_tr.select_one('td.hidden-xs > span')
        if not post_id_element:
            raise Exception('2CPU: 게시글 ID를 찾을 수 없습니다.')

        post_id_text = post_id_element.get_text(strip=True)
        if not post_id_text.isdigit():
            raise Exception(f'2CPU: 추출된 게시글 ID가 숫자가 아닙니다: "{post_id_text}"')
        post_id = int(post_id_text)

        # 두번째 td(hidden-xs)의 a에서 제목/링크 추출
        title_td = latest_post_tr.find_all('td', class_='hidden-xs')[1]
        title_element = title_td.find('a')
        title = title_element.get_text(strip=True)
        link = urljoin(self.url, title_element.get('href'))  # <-- 여기!

        return post_id, title, link

'''
참고사항
개발자 모드에서는 tbody 있음. HTML 파일에서는 tbody 없이 <tr class="is_notice">.
HTML에 tbody가 없으면 브라우저가 자동 생성해서 보여주기도 함.
하지만, requests로 가져온 HTML에는 tbody가 없을 수 있음.
BeautifulSoup이나 lxml도 HTML 파서를 쓸 때 tbody가 명시적으로 없으면, 자동으로 넣어주기도 하지만, 파싱 옵션이나 사이트의 미세구조에 따라 
tbody 없이 바로 table > tr로 잡힐 수도 있음.
항상 table > tr (또는 table > tbody > tr) 둘 다 대응하는 코드를 쓸 것.
실제 페이지에는 tbody가 없으므로, tbody 없이 <tr>로 검색하도록 수정.
'''