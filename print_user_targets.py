from telethon import TelegramClient
import os
import asyncio
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path, override=False)
else:
    print("No .env file found. Using system environment variables.")

TG_API_ID = os.getenv("TG_API_ID")
TG_API_HASH = os.getenv("TG_API_HASH")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

async def main():
    async with TelegramClient(os.path.join(DATA_DIR, "telegram_user_session"), TG_API_ID, TG_API_HASH) as client:
        async for dialog in client.iter_dialogs():
            print(dialog.name, dialog.id)

asyncio.run(main())
