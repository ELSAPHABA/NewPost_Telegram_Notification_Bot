import requests
from bs4 import BeautifulSoup

url = 'https://gall.dcinside.com/mgallery/board/lists/?id=minipc&sort_type=N&search_head=20&page=1'
headers = {
    'User-Agent': 'Mozilla/5.0'  # 사이트에서 봇 차단하는 경우 User-Agent 추가 필요
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# 원하는 tr을 CSS selector로 찾음 (두 번째 tr)
target_tr = soup.select_one(
    '#container > section.left_content > article:nth-child(3) > div.gall_listwrap.list > table > tbody > tr:nth-child(2)'
)

if target_tr:
    data_no = target_tr.get('data-no')
    print('data-no:', data_no)
else:
    print('해당 요소를 찾을 수 없습니다.')
