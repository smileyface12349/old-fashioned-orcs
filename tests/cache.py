import os
import pickle


class CacheManager:
    """Handles local storage of client."""

    async def load(self):
        """Loads cache file using pickle and returns it's contents."""
        try:
            with open("cache.dmp", "rb") as f:
                unique_id = pickle.load(f)
        except FileNotFoundError:
            unique_id = ""
        return unique_id

    async def save(self, unique_id: str):
        """Saves cache file using pickle."""
        with open("cache.dump", "wb") as f:
            pickle.dump(unique_id, f)

    async def delete(self):
        """Deletes local cache for whatever reason."""
        try:
            os.remove("cache.dmp")
        except OSError:
            pass
