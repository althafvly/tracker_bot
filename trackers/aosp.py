import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import logging
from typing import List, Set, Tuple
from .base import BaseTracker
from config import AOSP_REFS_URL, AOSP_BASE_URL

logger = logging.getLogger("trackerbot.trackers.aosp")

class AOSPTracker(BaseTracker):
    def __init__(self):
        super().__init__("AOSP")

    async def fetch_new_updates(self, saved_tags: Set[str]) -> List[Tuple[str, str]]:
        try:
            response = requests.get(AOSP_REFS_URL)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch AOSP tags: {e}")
            return []

        page = BeautifulSoup(response.content, "html.parser")
        tags = []

        for section in page.find_all("div", {"class": "RefList"}):
            title = section.find("h3", {"class": "RefList-title"})
            if title and "Tags" in title.text:
                for li in section.find_all("li"):
                    tag = li.text.strip()
                    if tag.startswith("android-security-") or tag.startswith("android-platform-"):
                        tags.append(tag)
                    if tag.startswith("android-15") or tag.startswith("android-16") or tag.startswith("android-17"):
                        tags.append(tag)

        groups = defaultdict(list)
        for tag in tags:
            if "_r" in tag:
                version, revision = tag.rsplit("_r", 1)
                groups[version].append(int(revision))
            else:
                groups[tag].append(0)

        latest_tags = {version: f"{version}_r{max(revs)}" for version, revs in groups.items()}
        sorted_latest = dict(sorted(latest_tags.items(), key=lambda x: x[0]))

        updates = []
        for version, tag in sorted_latest.items():
            key = f"AOSP:{tag}"
            if key not in saved_tags:
                url = f"{AOSP_BASE_URL}+/{'refs/tags/' + tag}"
                message = f'📱 <b>AOSP:</b> New tag <code>{tag}</code> detected!\n🔗 <a href="{url}">Check Here</a>'
                updates.append((key, message))

        return updates
