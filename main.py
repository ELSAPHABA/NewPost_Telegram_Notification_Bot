import requests
import time
import threading
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

class SiteWatcher:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.last_post_id = None
        self.interval = 30  # 기본 30초

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

    def send_telegram(self, bot, chat_id, text, link):
        bot.send_message(chat_id=chat_id, text=f"[{self.name}] 새 글: {text}\n{link}")

class DCGalleryWatcher(SiteWatcher):
    def get_latest_post(self):
        html = self.fetch_page()
        soup = BeautifulSoup(html, 'html.parser')
        tr = soup.select_one(
            '#container > section.left_content > article:nth-child(3) > div.gall_listwrap.list > table > tbody > tr:nth-child(3)'
        )
        if not tr:
            raise Exception('새글 tr을 찾을 수 없습니다.')
        post_id = tr.get('data-no')
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

class WatcherManager:
    def __init__(self, watcher, bot_token, chat_id):
        self.watcher = watcher
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.updater = Updater(token=bot_token, use_context=True)
        self.bot = self.updater.bot
        self.job = None
        self._add_handlers()
        self._start_thread()

    def _start_thread(self):
        # 텔레그램 updater와 별개로 watcher 루프를 별도 thread에서 동작
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()
        self.updater.start_polling()

    def run(self):
        while True:
            try:
                title, link = self.watcher.check_new_post()
                if title:
                    self.watcher.send_telegram(self.bot, self.chat_id, title, link)
                time.sleep(self.watcher.interval)
            except Exception as e:
                print("에러 발생:", e)
                time.sleep(self.watcher.interval)

    def _add_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('setinterval', self.set_interval))
        dp.add_handler(CommandHandler('interval', self.show_interval))
        dp.add_handler(CommandHandler('help', self.help_command))
        dp.add_handler(MessageHandler(Filters.text & (~Filters.command), self.echo_unknown))

    def set_interval(self, update, context):
        try:
            seconds = int(context.args[0])
            if not (5 <= seconds <= 3600):
                update.message.reply_text("5~3600초 범위로만 입력 가능.")
                return
            self.watcher.interval = seconds
            update.message.reply_text(f"새 글 확인 주기를 {seconds}초로 설정했습니다.")
        except Exception:
            update.message.reply_text("/setinterval [초] (예시: /setinterval 15)")

    def show_interval(self, update, context):
        update.message.reply_text(f"현재 확인 주기: {self.watcher.interval}초")

    def help_command(self, update, context):
        msg = (
            "/setinterval [초] : 새 글 확인 주기 변경 (기본 30초)\n"
            "/interval : 현재 주기 표시\n"
        )
        update.message.reply_text(msg)

    def echo_unknown(self, update, context):
        update.message.reply_text("명령어를 입력하세요. /help 참조")

# ========== 아래는 실제 실행 예시 ==========
if __name__ == "__main__":
    # 여기 정보 입력!
    BOT_TOKEN = '텔레그램봇토큰'
    CHAT_ID = 123456789  # 본인(혹은 그룹) chat_id

    watcher = DCGalleryWatcher(
        name="미니PC갤",
        url="https://gall.dcinside.com/mgallery/board/lists/?id=minipc&sort_type=N&search_head=20&page=1"
    )
    manager = WatcherManager(watcher, BOT_TOKEN, CHAT_ID)
    print("봇 및 크롤링 시작됨.")
    # 아래 라인은 생략해도 무방 (updater가 thread로 동작)
    # manager.updater.idle()