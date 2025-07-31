# main.py

import asyncio
from MiniPCWatcher import MiniPCWatcher
from SFFWatcher import SFFWatcher
from user_agents import UserAgentManager

from telegram.ext import Application, CommandHandler, ContextTypes

class WatcherManager:
    def __init__(self, watchers, chat_id, user_agent_manager):
        self.watchers = watchers
        self.chat_id = chat_id
        self.interval = 30  # 기본 주기(초)
        self.user_agent_manager = user_agent_manager

    async def check_watchers(self, context):
        bot = context.application.bot
        for watcher in self.watchers:
            try:
                watcher.interval = self.interval
                headers = {'User-Agent': self.user_agent_manager.get_user_agent()}
                title, link = watcher.check_new_post_with_headers(headers)
                if title:
                    await watcher.send_telegram(bot, self.chat_id, title, link)
            except Exception as e:
                print(f"{watcher.name} 크롤링 에러:", e)

    # 아래 핸들러 함수들은 모두 async!
    async def set_interval(self, update, context: ContextTypes.DEFAULT_TYPE):
        try:
            seconds = int(context.args[0])
            if not (5 <= seconds <= 3600):
                await update.message.reply_text("5~3600초 범위로만 입력 가능.")
                return
            self.interval = seconds
            await update.message.reply_text(f"새 글 확인 주기를 {seconds}초로 설정했습니다.")
            # interval 변경 시, job_queue의 interval도 업데이트
            jobs = context.application.job_queue.get_jobs_by_name('check_watchers')
            for job in jobs:
                job.schedule_removal()
            context.application.job_queue.run_repeating(self.check_watchers, interval=self.interval, name='check_watchers')
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
    manager = WatcherManager(watchers, CHAT_ID, ua_mgr)

    application = Application.builder().token(BOT_TOKEN).build()

    # job_queue에 크롤링 체크 job 등록
    application.job_queue.run_repeating(manager.check_watchers, interval=manager.interval, first=0, name='check_watchers')

    # 명령어 핸들러 등록
    application.add_handler(CommandHandler('setinterval', manager.set_interval))
    application.add_handler(CommandHandler('interval', manager.show_interval))
    application.add_handler(CommandHandler('setuainterval', manager.set_ua_interval))
    application.add_handler(CommandHandler('uainterval', manager.show_ua_interval))
    application.add_handler(CommandHandler('help', manager.help_command))

    print("봇 및 크롤링 시작됨.")
    application.run_polling()

    # 주의사항
    # python-telegram-bot 20.x/21.x는 apscheduler 3.9.x에 가장 잘 맞으며, apscheduler 3.x는 pytz만 완벽 지원합니다.
    # pip install apscheduler==3.9.1.post1
    # pip install pytz
    # pip install python-telegram-bot==20.7