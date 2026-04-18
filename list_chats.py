import asyncio
import logging
import sys
from telethon import TelegramClient
from config import TG_API_ID, TG_API_HASH, TELEGRAM_SESSION_FILE
from utils import logger

async def main():
    if not TG_API_ID or not TG_API_HASH:
        logger.error("TG_API_ID or TG_API_HASH not set in environment.")
        sys.exit(1)

    print(f"{'Name':<40} | {'ID':<15} | {'Type':<10}")
    print("-" * 70)

    try:
        async with TelegramClient(TELEGRAM_SESSION_FILE, int(TG_API_ID), TG_API_HASH) as client:
            async for dialog in client.iter_dialogs():
                chat_type = "User" if dialog.is_user else "Group" if dialog.is_group else "Channel"
                print(f"{str(dialog.name):<40} | {str(dialog.id):<15} | {chat_type:<10}")
    except Exception as e:
        logger.error(f"Failed to list dialogs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
