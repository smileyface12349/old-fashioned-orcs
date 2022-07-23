import os
import pickle


class CacheManager:
    """Handles local storage of client."""

    async def load(self):
        """Loads cache file using pickle and returns it's contents."""
        try:
            with open("cache.dmp", "rb") as f:
                payload = dict(pickle.load(f))
                payload["type"] = "ready"
        except FileNotFoundError:
            payload = {"type": "init", "unique_id": "", "nickname": ""}
        return payload

    async def save(self, payload: dict):
        """Saves cache file using pickle."""
        with open("cache.dmp", "wb") as f:
            data = {"unique_id": payload["unique_id"], "nickname": payload["nickname"]}
            pickle.dump(data, f)

    async def delete(self):
        """Deletes local cache for whatever reason."""
        try:
            os.remove("cache.dmp")
        except OSError:
            pass
