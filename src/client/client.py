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

        for _ in range(1000):
            while not established:
                payload = json.dumps(data)
                await websocket.send(payload)
                print(f"Sending => {payload}")

                response = await websocket.recv()
                response = json.loads(response)
                print(f"Response => {response}")

                if response["type"] in ["init", "ready", "action"]:
                    established = True
                    data["type"] = "ready"

                    if not data["unique_id"]:
                        # If user didnt have a unique_id, server returned him one
                        data["unique_id"] = response["unique_id"]

                    if not data["nickname"]:
                        # If user didnt specify a nickname, server returns a random one
                        data["nickname"] = response["nickname"]

                    if no_cache:
                        # If there is no cache saved, we need to create it
                        await cache.save(response)
                        no_cache = False

            else:
                # TODO => Play
                print("=> Playing..")

                data["position"] = 0, 0
                data["level"] = -1

                payload = json.dumps(data)
                await websocket.send(payload)
                print(f"Sending => {payload}")

                response = await websocket.recv()
                response = json.loads(response)
                print(f"Response => {response}")

            await asyncio.sleep(0.1)
        established = False


if __name__ == "__main__":
    asyncio.run(hello())
