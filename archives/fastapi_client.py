import asyncio
import json

import websockets
from cache import CacheManager

cache = CacheManager()


class ClientSession:
    """It handles ALL client/server interactions"""

    def __init__(self):
        self.status = "new"

    async def connect(self):
        """Typical client connection"""
        self.unique_id = await cache.load()
        no_cache = True if not self.unique_id else False

        async with websockets.connect("ws://localhost:8000/connect") as websocket:
            self.status = "online"

            payload = {"unique_id": self.unique_id}
            await websocket.send(json.dumps(payload))

            response = await websocket.recv()
            response = json.loads(response)

            print(self.status)
            print(f"Response => {response}")

            if no_cache:
                self.unique_id = response["unique_id"]
                await cache.save(self.unique_id)
                no_cache = False

    async def reconnect(self):
        """Typical client re-connection, same as connection but without cache checks."""
        async with websockets.connect("ws://localhost:8000/connect") as websocket:
            self.status = "reconnected"

            payload = {"unique_id": self.unique_id}
            await websocket.send(json.dumps(payload))

            response = await websocket.recv()
            response = json.loads(response)

            print(self.status)
            print(f"Response => {response}")

    async def disconnect(self):
        """Proper client disconnect, that will save & update status."""
        self.status = "disconnected"
        await cache.save(self.unique_id)
        print(self.status)


if __name__ == "__main__":
    client = ClientSession()
    asyncio.run(client.connect())
    asyncio.run(client.reconnect())
    asyncio.run(client.disconnect())
    asyncio.run(client.reconnect())
