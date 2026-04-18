import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path, override=False)
else:
    print("No .env file found. Using system environment variables.")

# Telegram Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TG_USER_ENABLED = os.getenv("TG_USER_ENABLED", "false").lower() == "true"
TG_API_ID = os.getenv("TG_API_ID")
TG_API_HASH = os.getenv("TG_API_HASH")
TG_USER_TARGETS = os.getenv("TG_USER_TARGETS", "")

# Service Configs
GITHUB_REPOS = os.getenv("GITHUB_REPOS", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITLAB_REPOS = os.getenv("GITLAB_REPOS", "")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

GENERIC_GIT_REPOS = os.getenv("GENERIC_GIT_REPOS", "")

# Application Config
_interval = os.getenv("CHECK_INTERVAL")
CHECK_INTERVAL = int(_interval) if _interval else None

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SAVED_TAGS_FILE = os.path.join(DATA_DIR, "saved_tags.txt")
TELEGRAM_SESSION_FILE = os.path.join(DATA_DIR, "telegram_user_session")

# Constants
AOSP_BASE_URL = "https://android.googlesource.com/platform/frameworks/base/"
AOSP_REFS_URL = AOSP_BASE_URL + "+refs"
GITHUB_API_URL = "https://api.github.com/repos"
GITLAB_API_URL = "https://gitlab.com/api/v4/projects"
CHROMIUM_DASH_URL = "https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Android&num=5"
