import requests
import logging
from typing import List, Set, Tuple
from .base import BaseTracker
from config import GITHUB_REPOS, GITHUB_TOKEN, GITHUB_API_URL

logger = logging.getLogger("trackerbot.trackers.github")

class GitHubTracker(BaseTracker):
    def __init__(self):
        super().__init__("GitHub")
        self.repos = [r.strip() for r in GITHUB_REPOS.split(",") if r.strip()]

    async def fetch_new_updates(self, saved_tags: Set[str]) -> List[Tuple[str, str]]:
        if not self.repos:
            return []

        updates = []
        headers = {"Accept": "application/vnd.github.v3+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        for repo in self.repos:
            try:
                url = f"{GITHUB_API_URL}/{repo}/tags"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                tags = response.json()
                if tags:
                    tag = tags[0]["name"]
                    key = f"GITHUB:{repo}:{tag}"
                    if key not in saved_tags:
                        repo_url = f"https://github.com/{repo}/releases/tag/{tag}"
                        message = f'🐙 <b>GitHub:</b> New tag <code>{tag}</code> in <b>{repo}</b>\n🔗 <a href="{repo_url}">Check Here</a>'
                        updates.append((key, message))
            except Exception as e:
                logger.error(f"Failed to fetch GitHub tags for {repo}: {e}")

        return updates
