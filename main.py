import requests
import time
import threading
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# 베이스 클래스 (불변)
class SiteWatcher:
    def __init__(self):
        self.name = None
        self.url = None
        self.last_post_id = None
        self.interval = 30

    def fetch_page(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_latest_post(self):
        raise NotImplementedError

    def check_new_post(self):
        post_id, title, link = self.get_latest_post()
        if self.last_post_id != post_id:
            self.last_post_id = post_id
            return title, link
        return None, None

    def send_telegram(self, bot, chat_id, text, link):
        bot.send_message(chat_id=chat_id, text=f"[{self.name}] 새 글: {text}\n{link}")

# 갤러리 별 크롤러 클래스들
class MiniPCWatcher(SiteWatcher):
    def __init__(self):
        super().__init__()
        self.name = "MiniPC"
        self.url = "https://gall.dcinside.com/mgallery/board/lists/?id=minipc&sort_type=N&search_head=20&page=1"

    def get_latest_post(self):
        html = self.fetch_page()
        soup = BeautifulSoup(html, 'html.parser')
        tr = soup.select_one(
            '#container > section.left_content > article:nth-child(3) > div.gall_listwrap.list > table > tbody > tr:nth-child(3)'
        )
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

class SFFWatcher(SiteWatcher):
    def __init__(self):
        super().__init__()
        self.name = "SFF"
        self.url = "https://gall.dcinside.com/mgallery/board/lists/?id=sff&sort_type=N&search_head=100&page=1"

    def get_latest_post(self):
        html = self.fetch_page()
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

# WatcherManager: 여러 Watcher를 하나의 봇, 하나의 loop에서 관리
class WatcherManager:
    def __init__(self, watchers, bot_token, chat_id):
        self.watchers = watchers  # 리스트 형태로 받음!
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.interval = 30  # 모든 watcher에 기본 적용, 필요시 개별 변경도 가능
        self.updater = Updater(token=bot_token, use_context=True)
        self.bot = self.updater.bot
        self._add_handlers()
        self._start_thread()

    def _start_thread(self):
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()
        self.updater.start_polling()

    def run(self):
        while True:
            for watcher in self.watchers:
                try:
                    watcher.interval = self.interval  # 관리자에서 한 번에 통제 (원하면 watcher별 세분화도 가능)
                    title, link = watcher.check_new_post()
                    if title:
                        watcher.send_telegram(self.bot, self.chat_id, title, link)
                except Exception as e:
                    print(f"{watcher.name} 크롤링 에러:", e)
            time.sleep(self.interval)

    def _add_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('setinterval', self.set_interval))
        dp.add_handler(CommandHandler('interval', self.show_interval))
        dp.add_handler(CommandHandler('help', self.help_command))

    def set_interval(self, update, context):
        try:
            seconds = int(context.args[0])
            if not (5 <= seconds <= 3600):
                update.message.reply_text("5~3600초 범위로만 입력 가능.")
                return
            self.interval = seconds
            update.message.reply_text(f"새 글 확인 주기를 {seconds}초로 설정했습니다.")
        except Exception:
            update.message.reply_text("/setinterval [초] (예시: /setinterval 15)")

    def show_interval(self, update, context):
        update.message.reply_text(f"현재 확인 주기: {self.interval}초")

    def help_command(self, update, context):
        msg = (
            "/setinterval [초] : 새 글 확인 주기 변경 (기본 30초)\n"
            "/interval : 현재 주기 표시\n"
        )
        update.message.reply_text(msg)

# ========= main 함수 ==========
if __name__ == "__main__":
    BOT_TOKEN = '텔레그램봇토큰'
    CHAT_ID = 123456789

    watchers = [MiniPCWatcher(), SFFWatcher()]
    manager = WatcherManager(watchers, BOT_TOKEN, CHAT_ID)
    print("봇 및 크롤링 시작됨.")
    try:
        while True:
            time.sleep(1)  # 메인 스레드가 종료되지 않도록 유지
    except KeyboardInterrupt:
        print("프로그램 종료")
        manager.updater.stop()