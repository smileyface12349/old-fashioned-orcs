import os
import pickle


class CacheManager:
    """Handles local storage of client."""

    @staticmethod
    async def load():
        """Loads cache file using pickle and returns it's contents."""
        try:
            with open("cache.dmp", "rb") as f:
                payload = dict(pickle.load(f))
                payload["type"] = "ready"
                payload["direction"] = "r"
        except FileNotFoundError:
            payload = {"type": "init", "unique_id": "", "nickname": "", "direction": "r"}
        return payload

    @staticmethod
    def get_nickname():
        """Check if the user already has a nickname."""
        try:
            with open("cache.dmp", "rb") as f:
                nick = dict(pickle.load(f))["nickname"]
            return nick if nick else None
        except FileNotFoundError:
            return None

    @staticmethod
    async def save(payload: dict):
        """Saves cache file using pickle."""
        with open("cache.dmp", "wb") as f:
            data = {"unique_id": payload["unique_id"], "nickname": payload["nickname"]}
            pickle.dump(data, f)

    @staticmethod
    def delete():
        """Deletes local cache for whatever reason."""
        try:
            os.remove("cache.dmp")
        except OSError:
            pass
