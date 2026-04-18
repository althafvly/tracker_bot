from abc import ABC, abstractmethod
from typing import List, Set, Tuple

class BaseTracker(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def fetch_new_updates(self, saved_tags: Set[str]) -> List[Tuple[str, str]]:
        """
        Fetches new updates.
        Returns a list of tuples: (unique_key, notification_message)
        """
        pass
