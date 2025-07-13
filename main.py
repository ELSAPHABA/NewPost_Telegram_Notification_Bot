# main.py

import time
import threading
from MiniPCWatcher import MiniPCWatcher
from SFFWatcher import SFFWatcher
from user_agents import UserAgentManager
from telegram.ext import Updater, CommandHandler

# WatcherManager 클래스
class WatcherManager:
    def __init__(self, watchers, bot_token, chat_id, user_agent_manager):
        self.watchers = watchers
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.interval = 30  # 새글 확인 주기(초)
        self.user_agent_manager = user_agent_manager
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
                    watcher.interval = self.interval
                    # user-agent를 세탁 매니저에서 받아옴
                    headers = {'User-Agent': self.user_agent_manager.get_user_agent()}
                    title, link = watcher.check_new_post_with_headers(headers)
                    if title:
                        watcher.send_telegram(self.bot, self.chat_id, title, link)
                except Exception as e:
                    print(f"{watcher.name} 크롤링 에러:", e)
            time.sleep(self.interval)

    def _add_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('setinterval', self.set_interval))
        dp.add_handler(CommandHandler('interval', self.show_interval))
        dp.add_handler(CommandHandler('setuainterval', self.set_ua_interval))  # User-Agent 세탁 주기 변경
        dp.add_handler(CommandHandler('uainterval', self.show_ua_interval))    # User-Agent 세탁 주기 조회
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
        update.message.reply_text(f"현재 새 글 확인 주기(초): {self.interval}")

    # --- User-Agent 세탁 주기 관련 텔레그램 명령 ---
    def set_ua_interval(self, update, context):
        try:
            n = int(context.args[0])
            self.user_agent_manager.set_interval(n)
            update.message.reply_text(f"User-Agent 세탁 주기를 {n}회로 설정했습니다.\n"
                                      f"(새 글 확인 {n}번마다 세탁됩니다)")
        except Exception:
            update.message.reply_text("/setuainterval [횟수] (예시: /setuainterval 20)")

    def show_ua_interval(self, update, context):
        cur = self.user_agent_manager.get_interval()
        update.message.reply_text(f"현재 User-Agent 세탁 주기: {cur}회\n(새 글 확인 {cur}번마다 세탁)")

    def help_command(self, update, context):
        msg = (
            "/setinterval [초] : 새 글 확인 주기 변경 (기본 30초)\n"
            "/interval : 현재 확인 주기(초) 표시\n"
            "/setuainterval [횟수] : User-Agent 세탁 주기 변경\n"
            "/uainterval : 현재 User-Agent 세탁 주기(횟수) 표시\n"
        )
        update.message.reply_text(msg)

# ========== main 실행 부분 ==========
if __name__ == "__main__":
    BOT_TOKEN = '텔레그램봇토큰'     # <- 본인 값으로 수정
    CHAT_ID = 123456789             # <- 본인(혹은 그룹) chat_id로 수정

    ua_mgr = UserAgentManager('user-agents.txt')  # 혹은 user-agents.csv
    watchers = [MiniPCWatcher(), SFFWatcher()]

    manager = WatcherManager(watchers, BOT_TOKEN, CHAT_ID, ua_mgr)
    print("봇 및 크롤링 시작됨.")
    try:
        while True:
            time.sleep(1)  # 메인 스레드 유지
    except KeyboardInterrupt:
        print("프로그램 종료")
        manager.updater.stop()
