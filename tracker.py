#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import os
import urllib.parse
import subprocess
from dotenv import load_dotenv, find_dotenv
from packaging import version as pkg_version
from packaging.version import Version

BASE_URL = "https://android.googlesource.com/platform/frameworks/base/"
REFS_URL = BASE_URL + "+refs"
GITHUB_API = "https://api.github.com/repos"
GITLAB_API = "https://gitlab.com/api/v4/projects"

dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path, override=False)
else:
    print("No .env file found. Using system environment variables.")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

GITHUB_REPOS = os.getenv("GITHUB_REPOS", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITLAB_REPOS = os.getenv("GITLAB_REPOS", "")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

GENERIC_GIT_REPOS = os.getenv("GENERIC_GIT_REPOS", "")

# Get directory where the script is located (root folder)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SAVED_TAGS_FILE = os.path.join(DATA_DIR, "saved_tags.txt")

def fetch_latest_security_tags():
    response = requests.get(REFS_URL)
    response.raise_for_status()

    page = BeautifulSoup(response.content, "html.parser")
    tags = []

    for section in page.find_all("div", {"class": "RefList"}):
        title = section.find("h3", {"class": "RefList-title"})
        if title and "Tags" in title.text:
            for li in section.find_all("li"):
                tag = li.text.strip()
                if tag.startswith("android-security-") or tag.startswith("android-platform-"):
                    tags.append(tag)
                if tag.startswith("android-15") or tag.startswith("android-16"):
                    tags.append(tag)

    groups = defaultdict(list)
    for tag in tags:
        if "_r" in tag:
            version, revision = tag.rsplit("_r", 1)
            groups[version].append(int(revision))
        else:
            groups[tag].append(0)

    latest_tags = {version: f"{version}_r{max(revs)}" for version, revs in groups.items()}
    return dict(sorted(latest_tags.items(), key=lambda x: x[0]))

def fetch_latest_github_tags():
    latest_tags = {}
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    for repo in [r.strip() for r in GITHUB_REPOS.split(",") if r.strip()]:
        url = f"{GITHUB_API}/{repo}/tags"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tags = response.json()
        if tags:
            latest_tags[repo] = tags[0]["name"]
    return latest_tags

def fetch_latest_gitlab_tags():
    latest_tags = {}
    headers = {"Accept": "application/json"}
    if GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = GITLAB_TOKEN

    for repo in [r.strip() for r in GITLAB_REPOS.split(",") if r.strip()]:
        project = urllib.parse.quote_plus(repo)
        url = f"{GITLAB_API}/{project}/repository/tags"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tags = response.json()
        if tags:
            latest_tags[repo] = tags[0]["name"]
    return latest_tags

def fetch_latest_git_tags(repo_url):
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
        if tags:
            tags = sorted(tags, key=safe_version_parse)
        return tags
    except Exception as e:
        print(f"Failed to fetch tags from {repo_url}: {e}")
        return []

def safe_version_parse(tag: str):
    """Try to parse as semantic version, otherwise return the raw tag for fallback sorting."""
    tag_clean = tag.lstrip('v')
    try:
        return pkg_version.parse(tag_clean)
    except Exception:
        # fallback: ensure non-semver tags still sort consistently
        return pkg_version.parse("0")  # put unknowns at the bottom

def load_saved_tags():
    if not os.path.exists(SAVED_TAGS_FILE):
        return set()
    with open(SAVED_TAGS_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_tags(tags):
    with open(SAVED_TAGS_FILE, "w") as f:
        for tag in sorted(tags):
            f.write(tag + "\n")

def fetch_latest_chromium_android_stable():
    """Fetch the latest Chromium stable version for Android."""
    url = "https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Android&num=5"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list):
            versions = [item.get("version") for item in data if item.get("version")]
            if versions:
                return max(versions, key=Version)   # take the highest version

    except Exception as e:
        print(f"Failed to fetch Chromium Android stable version: {e}")

    return None

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Support multiple chat IDs (comma-separated string)
    chat_ids = [chat_id.strip() for chat_id in CHAT_ID.split(",") if chat_id.strip()]
    
    for chat_id in chat_ids:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()

if __name__ == "__main__":
    saved_tags = load_saved_tags()
    new_tags = set()

    # --- AOSP Tags ---
    latest_aosp_tags = fetch_latest_security_tags()
    for version, tag in latest_aosp_tags.items():
        key = f"AOSP:{tag}"
        if key not in saved_tags:
            url = f"{BASE_URL}+/{'refs/tags/' + tag}"
            message = f'New AOSP tag detected! {tag}\n<a href="{url}">Check Here</a>'
            send_telegram_message(message)
            new_tags.add(key)

    # --- GitHub Tags ---
    if GITHUB_REPOS:
        github_tags = fetch_latest_github_tags()
        for repo, tag in github_tags.items():
            key = f"GITHUB:{repo}:{tag}"
            if key not in saved_tags:
                repo_url = f"https://github.com/{repo}/releases/tag/{tag}"
                message = f'New GitHub tag detected in <b>{repo}</b>: {tag}\n<a href="{repo_url}">Check Here</a>'
                send_telegram_message(message)
                new_tags.add(key)

    # --- GitLab Tags ---
    if GITLAB_REPOS:
        gitlab_tags = fetch_latest_gitlab_tags()
        for repo, tag in gitlab_tags.items():
            key = f"GITLAB:{repo}:{tag}"
            if key not in saved_tags:
                repo_url = f"https://gitlab.com/{repo}/-/tags/{tag}"
                message = f'New GitLab tag detected in <b>{repo}</b>: {tag}\n<a href="{repo_url}">Check Here</a>'
                send_telegram_message(message)
                new_tags.add(key)

    # --- Generic Git Tags (SourceForge, Bitbucket, etc.) ---
    if GENERIC_GIT_REPOS:
        for repo_url in [r.strip() for r in GENERIC_GIT_REPOS.split(",") if r.strip()]:
            tags = fetch_latest_git_tags(repo_url)
            if tags:
                latest_tag = tags[-1]  # newest semantically sorted tag
                key = f"GENERIC:{repo_url}:{latest_tag}"
                if key not in saved_tags:
                    # Try to detect if it's a SourceForge repo
                    if "git.code.sf.net" in repo_url:
                        # Extract project name: https://git.code.sf.net/p/<project>/code
                        parts = repo_url.split("/")
                        project = parts[4] if len(parts) > 4 else "unknown"
                        repo_url_display = f"https://sourceforge.net/p/{project}/code/ci/{latest_tag}/tree/"
                    else:
                        repo_url_display = repo_url  # fallback: raw repo URL

                    message = (
                        f'New Git tag detected in <b>{project}</b>: {latest_tag}\n'
                        f'<a href="{repo_url_display}">Check Here</a>'
                    )
                    send_telegram_message(message)
                    new_tags.add(key)

    # --- Chromium Android Stable ---
    chromium_version = fetch_latest_chromium_android_stable()
    if chromium_version:
        key = f"CHROMIUM_ANDROID:{chromium_version}"
        if key not in saved_tags:
            url = f"https://chromium.googlesource.com/chromium/src/+/refs/tags/{chromium_version}"
            message = (
                f'New Chromium Android Stable version detected: <b>{chromium_version}</b>\n'
                f'<a href="{url}">Check Here</a>'
            )
            send_telegram_message(message)
            new_tags.add(key)

    # Save combined tags
    all_tags = saved_tags.union(new_tags)
    save_tags(all_tags)

