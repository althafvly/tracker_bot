#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import os
from dotenv import load_dotenv

BASE_URL = "https://android.googlesource.com/platform/frameworks/base/"
REFS_URL = BASE_URL + "+refs"

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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
    latest_tags = fetch_latest_security_tags()
    saved_tags = load_saved_tags()

    new_tags = {tag for version, tag in latest_tags.items() if tag not in saved_tags}

    for tag in new_tags:
        url = f"{BASE_URL}+/{'refs/tags/' + tag}"
        message = f'New tag detected! {tag}\n<a href="{url}">Check Here</a>'
        send_telegram_message(message)

    # Update saved tags with latest tags
    all_tags = saved_tags.union({tag for version, tag in latest_tags.items()})
    save_tags(all_tags)
