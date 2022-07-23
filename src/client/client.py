import asyncio
import json

import websockets
from cache import CacheManager

cache = CacheManager()


async def hello():
    """Typical client connection"""
    data = await cache.load()
    no_cache = True if not all(data.values()) else False

    async with websockets.connect("ws://localhost:8000/") as websocket:

        if not data["nickname"]:
            data["nickname"] = input("Enter a nickname.")
        payload = json.dumps(data)
        await websocket.send(payload)
        print(f"Sending => {payload}")

        response = await websocket.recv()
        response = json.loads(response)
        print(f"Response => {response}")

        if no_cache:
            await cache.save(response)
            no_cache = False


if __name__ == "__main__":
    asyncio.run(hello())
