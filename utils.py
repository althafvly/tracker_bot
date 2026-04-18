import os
import logging
from packaging import version as pkg_version
from config import SAVED_TAGS_FILE

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("trackerbot")

def safe_version_parse(tag: str):
    """Try to parse as semantic version, otherwise return the raw tag for fallback sorting."""
    tag_clean = tag.lstrip('v')
    try:
        return pkg_version.parse(tag_clean)
    except Exception:
        # fallback: ensure non-semver tags still sort consistently
        return pkg_version.parse("0")  # put unknowns at the bottom

def load_saved_tags() -> set[str]:
    if not os.path.exists(SAVED_TAGS_FILE):
        return set()
    with open(SAVED_TAGS_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_tags(tags: set[str]):
    with open(SAVED_TAGS_FILE, "w") as f:
        for tag in sorted(tags):
            f.write(tag + "\n")
