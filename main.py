# main.py

import logging
from config import get_settings
from MiniPCWatcher import MiniPCWatcher
from SBNordVPNWatcher import SBNordVPNWatcher
from SFFWatcher import SFFWatcher
from SBSurfsharkWatcher import SBSurfsharkWatcher
from SSAdguardWatcher import SSAdguardWatcher
from TwoCPUWatcher import TwoCPUWatcher
from user_agents import UserAgentManager
from Telegram_bot import ChatIdManager, WatcherManager, register_user
from dotenv import load_dotenv

load_dotenv()

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = get_settings()

    chat_id_mgr = ChatIdManager(settings.chat_ids_file)
    ua_mgr = UserAgentManager(
        settings.user_agents_file,
        rotate_interval=settings.user_agent_rotate_interval,
    )
    watchers = [
        MiniPCWatcher(),
        SFFWatcher(),
        TwoCPUWatcher(),
        SBNordVPNWatcher(),
        SBSurfsharkWatcher(),
        SSAdguardWatcher(),
    ]
    manager = WatcherManager(
        watchers,
        chat_id_mgr,
        ua_mgr,
        worker_count=settings.watcher_worker_count,
    )

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data['chat_id_manager'] = chat_id_mgr

    application.job_queue.run_repeating(manager.check_watchers, interval=manager.interval, first=0, name='check_watchers')
    
    application.add_handler(MessageHandler(filters.COMMAND, register_user), group=-1)

    application.add_handler(CommandHandler('start', manager.start))
    application.add_handler(CommandHandler('setinterval', manager.set_interval))
    application.add_handler(CommandHandler('interval', manager.show_interval))
    application.add_handler(CommandHandler('setuainterval', manager.set_ua_interval))
    application.add_handler(CommandHandler('uainterval', manager.show_ua_interval))
    application.add_handler(CommandHandler('help', manager.help_command))
    application.add_handler(CommandHandler('restart', manager.restart))

    logging.info("봇 및 크롤링 시작됨.")
    application.run_polling()
