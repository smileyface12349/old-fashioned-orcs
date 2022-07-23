import asyncio
import json

import websockets
from cache import CacheManager

cache = CacheManager()


async def hello():
    """Typical client connection"""
    established = False
    data = await cache.load()
    no_cache = True if not all(data.values()) else False

    if not data["nickname"]:
        data["nickname"] = input("Enter a nickname: ")

    async with websockets.connect("ws://localhost:8000/") as websocket:

        for _ in range(15):
            while not established:
                payload = json.dumps(data)
                await websocket.send(payload)
                print(f"Sending => {payload}")

                response = await websocket.recv()
                response = json.loads(response)
                print(f"Response => {response}")

                if response["type"] == "ready":
                    established = True
                    if no_cache:
                        await cache.save(response)
                        no_cache = False

            else:
                # TODO => Play
                print("=> Playing..")

                data["position"] = 0, 0
                data["level"] = 0

                payload = json.dumps(data)
                await websocket.send(payload)
                print(f"Sending => {payload}")

                response = await websocket.recv()
                response = json.loads(response)
                print(f"Response => {response}")

            await asyncio.sleep(0.3)


if __name__ == "__main__":
    asyncio.run(hello())
