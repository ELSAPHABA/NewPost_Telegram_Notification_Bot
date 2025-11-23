# main.py

import asyncio
import json
import logging
import os
from MiniPCWatcher import MiniPCWatcher
from SFFWatcher import SFFWatcher
from TwoCPUWatcher import TwoCPUWatcher
from user_agents import UserAgentManager

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import Forbidden, BadRequest

# 1. ChatIdManager 클래스 추가: chat_id 목록을 파일로 관리
class ChatIdManager:
    def __init__(self, filepath='chat_ids.json'):
        self.filepath = filepath
        self.chat_ids = self._load_ids()

    def _load_ids(self):
        if not os.path.exists(self.filepath):
            return set()
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                return set(data)
        except (json.JSONDecodeError, FileNotFoundError):
            return set()

    def _save_ids(self):
        with open(self.filepath, 'w') as f:
            json.dump(list(self.chat_ids), f)

    def add_id(self, chat_id):
        if chat_id not in self.chat_ids:
            self.chat_ids.add(chat_id)
            self._save_ids()
            logging.info(f"새로운 chat_id {chat_id}가 등록되었습니다.")
            return True
        return False

    def remove_id(self, chat_id):
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
            self._save_ids()
            logging.info(f"chat_id {chat_id}가 제거되었습니다.")

    def get_ids(self):
        return list(self.chat_ids)

class WatcherManager:
    # 2. chat_id 대신 chat_id_manager를 받도록 수정
    def __init__(self, watchers, chat_id_manager, user_agent_manager):
        self.watchers = watchers
        self.chat_id_manager = chat_id_manager
        self.interval = 30
        self.user_agent_manager = user_agent_manager

    # 3. 모든 사용자에게 알림을 보내고, 실패 시 목록에서 제거하도록 수정
    async def check_watchers(self, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        for watcher in self.watchers:
            try:
                watcher.interval = self.interval
                headers = {'User-Agent': self.user_agent_manager.get_user_agent()}
                title, link = watcher.check_new_post_with_headers(headers)
                if title:
                    ids_to_remove = []
                    for chat_id in self.chat_id_manager.get_ids():
                        try:
                            await watcher.send_telegram(bot, chat_id, title, link)
                        except (Forbidden, BadRequest) as e:
                            error_msg = str(e).lower()
                            if "chat not found" in error_msg or "bot was blocked" in error_msg or "user is deactivated" in error_msg:
                                logging.warning(f"메시지 전송 실패로 chat_id {chat_id}를 제거합니다: {e}")
                                ids_to_remove.append(chat_id)
                            else:
                                logging.error(f"chat_id {chat_id}로 메시지 전송 중 에러 발생: {e}")
                    
                    for chat_id in ids_to_remove:
                        self.chat_id_manager.remove_id(chat_id)

            except Exception as e:
                logging.error(f"{watcher.name} 크롤링 에러: {e}")

    async def set_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            seconds = int(context.args[0])
            if not (5 <= seconds <= 3600):
                await update.message.reply_text("5~3600초 범위로만 입력 가능.")
                return
            self.interval = seconds
            await update.message.reply_text(f"새 글 확인 주기를 {seconds}초로 설정했습니다.")

            jobs = context.application.job_queue.get_jobs_by_name('check_watchers')
            for job in jobs:
                await job.schedule_removal()
            context.application.job_queue.run_repeating(
                self.check_watchers, interval=self.interval, first=0, name='check_watchers'
            )
        except (IndexError, ValueError):
            await update.message.reply_text("/setinterval [초] (예시: /setinterval 15)")

    async def show_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"현재 새 글 확인 주기(초): {self.interval}")

    async def set_ua_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            n = int(context.args[0])
            self.user_agent_manager.set_interval(n)
            await update.message.reply_text(
                f"User-Agent 세탁 주기를 {n}회로 설정했습니다.\n(새 글 확인 {n}번마다 세탁됩니다)"
            )
        except (IndexError, ValueError):
            await update.message.reply_text("/setuainterval [횟수] (예시: /setuainterval 20)")

    async def show_ua_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        cur = self.user_agent_manager.get_interval()
        await update.message.reply_text(
            f"현재 User-Agent 세탁 주기: {cur}회\n(새 글 확인 {cur}번마다 세탁)"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = (
            "/start : 새 글 알림 구독 시작\n"
            "/setinterval [초] : 새 글 확인 주기 변경 (기본 30초)\n"
            "/interval : 현재 확인 주기(초) 표시\n"
            "/setuainterval [횟수] : User-Agent 세탁 주기 변경\n"
            "/uainterval : 현재 User-Agent 세탁 주기(횟수) 표시\n"
            "/help : 도움말 보기"
        )
        await update.message.reply_text(msg)
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if self.chat_id_manager.add_id(chat_id):
            await update.message.reply_text("새 글 알림 구독을 시작합니다. 새 글이 올라올 때마다 알려드리겠습니다.")
        else:
            await update.message.reply_text("이미 새 글 알림을 구독하고 있습니다.")

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        context.bot_data['chat_id_manager'].add_id(update.message.chat_id)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    BOT_TOKEN = '7049762468:AAGo32N485eDBpgMuIRNhS9XUgC6Ydtk8bA'

    # 4. ChatIdManager 인스턴스 생성 및 WatcherManager에 전달
    chat_id_mgr = ChatIdManager('chat_ids.json')
    ua_mgr = UserAgentManager('user-agents.txt')
    watchers = [MiniPCWatcher(), SFFWatcher(), TwoCPUWatcher()]
    manager = WatcherManager(watchers, chat_id_mgr, ua_mgr)

    application = Application.builder().token(BOT_TOKEN).build()
    application.bot_data['chat_id_manager'] = chat_id_mgr

    application.job_queue.run_repeating(manager.check_watchers, interval=manager.interval, first=0, name='check_watchers')
    
    # 5. 모든 명령어에 대해 chat_id를 등록하는 핸들러 추가
    application.add_handler(MessageHandler(filters.COMMAND, register_user), group=-1)

    # 6. 명령어 핸들러 등록
    application.add_handler(CommandHandler('start', manager.start))
    application.add_handler(CommandHandler('setinterval', manager.set_interval))
    application.add_handler(CommandHandler('interval', manager.show_interval))
    application.add_handler(CommandHandler('setuainterval', manager.set_ua_interval))
    application.add_handler(CommandHandler('uainterval', manager.show_ua_interval))
    application.add_handler(CommandHandler('help', manager.help_command))

    logging.info("봇 및 크롤링 시작됨.")
    application.run_polling()