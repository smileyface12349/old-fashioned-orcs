import os
import pickle


class CacheManager:
    """Handles local storage of client."""

    async def load(self):
        """Loads cache file using pickle and returns it's contents."""
        try:
            with open("cache.dmp", "rb") as f:
                # unique_id = pickle.load(f)
                payload = dict(pickle.load(f))
        except FileNotFoundError:
            payload = {"nickname": "", "unique_id": ""}
        return payload

    async def save(self, payload: dict):
        """Saves cache file using pickle."""
        with open("cache.dmp", "wb") as f:
            pickle.dump(payload, f)

    async def delete(self):
        """Deletes local cache for whatever reason."""
        try:
            os.remove("cache.dmp")
        except OSError:
            pass
