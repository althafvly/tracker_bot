import requests
import urllib.parse
import logging
from typing import List, Set, Tuple
from .base import BaseTracker
from config import GITLAB_REPOS, GITLAB_TOKEN, GITLAB_API_URL

logger = logging.getLogger("trackerbot.trackers.gitlab")

class GitLabTracker(BaseTracker):
    def __init__(self):
        super().__init__("GitLab")
        self.repos = [r.strip() for r in GITLAB_REPOS.split(",") if r.strip()]

    async def fetch_new_updates(self, saved_tags: Set[str]) -> List[Tuple[str, str]]:
        if not self.repos:
            return []

        updates = []
        headers = {"Accept": "application/json"}
        if GITLAB_TOKEN:
            headers["PRIVATE-TOKEN"] = GITLAB_TOKEN

        for repo in self.repos:
            try:
                project = urllib.parse.quote_plus(repo)
                url = f"{GITLAB_API_URL}/{project}/repository/tags"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                tags = response.json()
                if tags:
                    tag = tags[0]["name"]
                    key = f"GITLAB:{repo}:{tag}"
                    if key not in saved_tags:
                        repo_url = f"https://gitlab.com/{repo}/-/tags/{tag}"
                        message = f'🦊 <b>GitLab:</b> New tag <code>{tag}</code> in <b>{repo}</b>\n🔗 <a href="{repo_url}">Check Here</a>'
                        updates.append((key, message))
            except Exception as e:
                logger.error(f"Failed to fetch GitLab tags for {repo}: {e}")

        return updates
