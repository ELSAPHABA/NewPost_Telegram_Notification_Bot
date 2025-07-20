# main.py

import time
import threading
import asyncio
from MiniPCWatcher import MiniPCWatcher
from SFFWatcher import SFFWatcher
from user_agents import UserAgentManager

from telegram.ext import Application, CommandHandler, ContextTypes

class WatcherManager:
    def __init__(self, watchers, bot_token, chat_id, user_agent_manager):
        self.watchers = watchers
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.interval = 30
        self.user_agent_manager = user_agent_manager
        self.application = Application.builder().token(self.bot_token).build()
        self._add_handlers()
        self._start_thread()

    def _start_thread(self):
        # Telegram polling을 비동기로 실행
        threading.Thread(target=self._run_polling, daemon=True).start()
        # Watcher 감시 루프(비동기)를 별도 스레드에서 실행
        threading.Thread(target=self._run_watcher_loop, daemon=True).start()

    def _run_polling(self):
        asyncio.run(self.application.run_polling())

    def _run_watcher_loop(self):
        # 봇 인스턴스는 application.bot에서 가져옴
        bot = self.application.bot
        while True:
            for watcher in self.watchers:
                try:
                    watcher.interval = self.interval
                    headers = {'User-Agent': self.user_agent_manager.get_user_agent()}
                    title, link = watcher.check_new_post_with_headers(headers)
                    if title:
                        # send_telegram이 동기라면 동기로 호출, 비동기로 바꿀 경우 await 사용!
                        asyncio.run(watcher.send_telegram(bot, self.chat_id, title, link))
                except Exception as e:
                    print(f"{watcher.name} 크롤링 에러:", e)
            time.sleep(self.interval)

    def _add_handlers(self):
        app = self.application
        app.add_handler(CommandHandler('setinterval', self.set_interval))
        app.add_handler(CommandHandler('interval', self.show_interval))
        app.add_handler(CommandHandler('setuainterval', self.set_ua_interval))
        app.add_handler(CommandHandler('uainterval', self.show_ua_interval))
        app.add_handler(CommandHandler('help', self.help_command))

    # --- 모든 핸들러 함수는 async로! ---
    async def set_interval(self, update, context: ContextTypes.DEFAULT_TYPE):
        try:
            seconds = int(context.args[0])
            if not (5 <= seconds <= 3600):
                await update.message.reply_text("5~3600초 범위로만 입력 가능.")
                return
            self.interval = seconds
            await update.message.reply_text(f"새 글 확인 주기를 {seconds}초로 설정했습니다.")
        except Exception:
            await update.message.reply_text("/setinterval [초] (예시: /setinterval 15)")

    async def show_interval(self, update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"현재 새 글 확인 주기(초): {self.interval}")

    async def set_ua_interval(self, update, context: ContextTypes.DEFAULT_TYPE):
        try:
            n = int(context.args[0])
            self.user_agent_manager.set_interval(n)
            await update.message.reply_text(
                f"User-Agent 세탁 주기를 {n}회로 설정했습니다.\n(새 글 확인 {n}번마다 세탁됩니다)"
            )
        except Exception:
            await update.message.reply_text("/setuainterval [횟수] (예시: /setuainterval 20)")

    async def show_ua_interval(self, update, context: ContextTypes.DEFAULT_TYPE):
        cur = self.user_agent_manager.get_interval()
        await update.message.reply_text(
            f"현재 User-Agent 세탁 주기: {cur}회\n(새 글 확인 {cur}번마다 세탁)"
        )

    async def help_command(self, update, context: ContextTypes.DEFAULT_TYPE):
        msg = (
            "/setinterval [초] : 새 글 확인 주기 변경 (기본 30초)\n"
            "/interval : 현재 확인 주기(초) 표시\n"
            "/setuainterval [횟수] : User-Agent 세탁 주기 변경\n"
            "/uainterval : 현재 User-Agent 세탁 주기(횟수) 표시\n"
        )
        await update.message.reply_text(msg)

# ========== main 실행 부분 ==========
if __name__ == "__main__":
    BOT_TOKEN = '7049762468:AAGo32N485eDBpgMuIRNhS9XUgC6Ydtk8bA'
    CHAT_ID = 5002639138

    ua_mgr = UserAgentManager('user-agents.txt')
    watchers = [MiniPCWatcher(), SFFWatcher()]

    manager = WatcherManager(watchers, BOT_TOKEN, CHAT_ID, ua_mgr)
    print("봇 및 크롤링 시작됨.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("프로그램 종료")