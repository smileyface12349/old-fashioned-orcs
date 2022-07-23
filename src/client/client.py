import asyncio
import json

import websockets
from cache import CacheManager

cache = CacheManager()


async def hello():
    """Typical client connection"""
    unique_id = await cache.load()
    no_cache = True if not unique_id else False

    async with websockets.connect("ws://localhost:8000/") as websocket:

        payload = json.dumps({"unique_id": unique_id})
        await websocket.send(payload)
        print(f"Sending => {payload}")

        response = await websocket.recv()
        response = json.loads(response)
        print(f"Response => {response}")

        if no_cache:
            unique_id = response["unique_id"]
            await cache.save(unique_id)
            no_cache = False


if __name__ == "__main__":
    asyncio.run(hello())
