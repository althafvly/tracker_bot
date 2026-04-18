import subprocess
import logging
from typing import List, Set, Tuple
from .base import BaseTracker
from config import GENERIC_GIT_REPOS
from utils import safe_version_parse

logger = logging.getLogger("trackerbot.trackers.generic_git")

class GenericGitTracker(BaseTracker):
    def __init__(self):
        super().__init__("GenericGit")
        self.repos = [r.strip() for r in GENERIC_GIT_REPOS.split(",") if r.strip()]

    async def fetch_new_updates(self, saved_tags: Set[str]) -> List[Tuple[str, str]]:
        if not self.repos:
            return []

        updates = []
        for repo_url in self.repos:
            try:
                result = subprocess.run(
                    ["git", "ls-remote", "--tags", repo_url],
                    capture_output=True, text=True, check=True
                )
                tags = []
                for line in result.stdout.splitlines():
                    if "refs/tags/" in line:
                        tag = line.split("refs/tags/")[1]
                        tag = tag.replace("^{}", "")
                        tags.append(tag)

                if not tags:
                    continue

                # Sort by version and pick the newest
                sorted_tags = sorted(tags, key=safe_version_parse)
                latest_tag = sorted_tags[-1]

                key = f"GENERIC:{repo_url}:{latest_tag}"
                if key not in saved_tags:
                    display_url = repo_url
                    project_name = repo_url

                    # Special handling for SourceForge
                    if "git.code.sf.net" in repo_url:
                        parts = repo_url.split("/")
                        if len(parts) > 4:
                            project = parts[4]
                            project_name = project
                            display_url = f"https://sourceforge.net/p/{project}/code/ci/{latest_tag}/tree/"

                    message = (
                        f'🏷️ <b>Git Tag:</b> New tag <code>{latest_tag}</code> in <b>{project_name}</b>\n'
                        f'🔗 <a href="{display_url}">Check Here</a>'
                    )
                    updates.append((key, message))

            except Exception as e:
                logger.error(f"Failed to fetch generic git tags for {repo_url}: {e}")

        return updates
