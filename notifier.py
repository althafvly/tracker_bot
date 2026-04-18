import requests
import logging
from telethon import TelegramClient
from config import (
    TG_USER_ENABLED, TG_API_ID, TG_API_HASH, TG_USER_TARGETS,
    BOT_TOKEN, CHAT_ID, TELEGRAM_SESSION_FILE
)

logger = logging.getLogger("trackerbot.notifier")

class TelegramNotifier:
    def __init__(self):
        self.telethon_client = None
        if TG_USER_ENABLED and TG_API_ID and TG_API_HASH:
            self.telethon_client = TelegramClient(
                TELEGRAM_SESSION_FILE,
                int(TG_API_ID),
                TG_API_HASH
            )

    async def start(self):
        if self.telethon_client:
            await self.telethon_client.start()

    async def send_message(self, text: str):
        # --- USER ACCOUNT MODE ---
        if TG_USER_ENABLED and self.telethon_client:
            text_with_footer = text + "\n\n—\n🤖 <i>This is an automated message.</i>"
            targets = [c.strip() for c in TG_USER_TARGETS.split(",") if c.strip()]

            for target in targets:
                try:
                    # Handle both numeric IDs and usernames
                    if target.startswith('-') or target.isdigit():
                        entity = await self.telethon_client.get_entity(int(target))
                    else:
                        entity = await self.telethon_client.get_entity(target)

                    await self.telethon_client.send_message(
                        entity,
                        text_with_footer,
                        parse_mode="html",
                        link_preview=False
                    )
                    logger.info(f"Sent message to user entity {target}: {text.splitlines()[0]}")
                except Exception as e:
                    logger.error(f"Failed to send message to user entity {target}: {e}")
            return

        # --- BOT MODE ---
        if not BOT_TOKEN or not CHAT_ID:
            logger.warning("Telegram Bot Token or Chat ID not configured.")
            return

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        chat_ids = [chat_id.strip() for chat_id in CHAT_ID.split(",") if chat_id.strip()]

        for chat_id in chat_ids:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            try:
                response = requests.post(url, data=payload)
                response.raise_for_status()
                logger.info(f"Sent message to chat {chat_id}: {text.splitlines()[0]}")
            except Exception as e:
                logger.error(f"Failed to send message to chat {chat_id}: {e}")

notifier = TelegramNotifier()
