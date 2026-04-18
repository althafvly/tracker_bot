import asyncio
import logging
import sys
from config import CHECK_INTERVAL
from utils import load_saved_tags, save_tags, logger
from notifier import notifier
from trackers.aosp import AOSPTracker
from trackers.github import GitHubTracker
from trackers.gitlab import GitLabTracker
from trackers.chromium import ChromiumTracker
from trackers.generic_git import GenericGitTracker

async def run_trackers():
    saved_tags = load_saved_tags()
    new_keys = set()

    trackers = [
        AOSPTracker(),
        GitHubTracker(),
        GitLabTracker(),
        ChromiumTracker(),
        GenericGitTracker()
    ]

    # Run all trackers concurrently
    tasks = [tracker.fetch_new_updates(saved_tags) for tracker in trackers]
    results = await asyncio.gather(*tasks)

    for tracker_results in results:
        for key, message in tracker_results:
            await notifier.send_message(message)
            new_keys.add(key)

    if new_keys:
        all_tags = saved_tags.union(new_keys)
        save_tags(all_tags)
        logger.info(f"Detected {len(new_keys)} new updates.")
    else:
        logger.info("No new updates detected.")

async def main():
    # Initialize notifier (starts Telethon if enabled)
    await notifier.start()

    if not CHECK_INTERVAL:
        await run_trackers()
        return

    logger.info(f"Loop mode enabled (interval: {CHECK_INTERVAL}s). Starting tracker...")
    while True:
        try:
            await run_trackers()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")

        logger.info(f"Sleeping for {CHECK_INTERVAL}s...")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Tracker stopped by user.")
        sys.exit(0)
