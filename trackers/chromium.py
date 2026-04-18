import requests
import logging
from packaging.version import Version
from typing import List, Set, Tuple
from .base import BaseTracker
from config import CHROMIUM_DASH_URL

logger = logging.getLogger("trackerbot.trackers.chromium")

class ChromiumTracker(BaseTracker):
    def __init__(self):
        super().__init__("Chromium")

    async def fetch_new_updates(self, saved_tags: Set[str]) -> List[Tuple[str, str]]:
        try:
            response = requests.get(CHROMIUM_DASH_URL)
            response.raise_for_status()
            data = response.json()

            if data and isinstance(data, list):
                versions = [item.get("version") for item in data if item.get("version")]
                if versions:
                    latest_version = max(versions, key=Version)
                    key = f"CHROMIUM_ANDROID:{latest_version}"
                    if key not in saved_tags:
                        url = f"https://chromium.googlesource.com/chromium/src/+/refs/tags/{latest_version}"
                        message = (
                            f'🌐 <b>Chromium:</b> New Android Stable version <code>{latest_version}</code>\n'
                            f'🔗 <a href="{url}">Check Here</a>'
                        )
                        return [(key, message)]

        except Exception as e:
            logger.error(f"Failed to fetch Chromium Android stable version: {e}")

        return []
