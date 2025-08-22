#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import os
import urllib.parse
from dotenv import load_dotenv

BASE_URL = "https://android.googlesource.com/platform/frameworks/base/"
REFS_URL = BASE_URL + "+refs"
GITHUB_API = "https://api.github.com/repos"
GITLAB_API = "https://gitlab.com/api/v4/projects"

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

GITHUB_REPOS = os.getenv("GITHUB_REPOS", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITLAB_REPOS = os.getenv("GITLAB_REPOS", "")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# Get directory where the script is located (root folder)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_TAGS_FILE = os.path.join(ROOT_DIR, "saved_tags.txt")

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

def load_saved_tags():
    if not os.path.exists(SAVED_TAGS_FILE):
        return set()
    with open(SAVED_TAGS_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_tags(tags):
    with open(SAVED_TAGS_FILE, "w") as f:
        for tag in sorted(tags):
            f.write(tag + "\n")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
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

    # Save combined tags
    all_tags = saved_tags.union(new_tags)
    save_tags(all_tags)

