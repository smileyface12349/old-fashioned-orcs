import asyncio
import json

import websockets
from cache import CacheManager

cache = CacheManager()


async def hello(websocket, cache_data):
    """Typical client/server hello connection"""
    no_cache = True if not all(cache_data.values()) else False

    hi = json.dumps(cache_data)
    await websocket.send(hi)
    print(f"Sending => {hi}")

    response = await websocket.recv()
    response = json.loads(response)
    print(f"Response => {response}")

    if response["type"] in ["init", "ready"]:

        if not cache_data["unique_id"]:
            # If user didnt have a unique_id, server returned him one
            cache_data["unique_id"] = response["unique_id"]

        if not cache_data["nickname"]:
            # If user didnt specify a nickname, server returns a random one
            cache_data["nickname"] = response["nickname"]

        if no_cache:
            # If there is no cache saved, we need to create it
            await cache.save(response)
            no_cache = False
        return cache_data

    else:
        raise Exception("Invalid type in response")


async def play(websocket, payload):
    """TODO => actually play"""
    payload["type"] = "play"

    for _ in range(1000):
        # Update the payload with real data
        print("=> Playing..")

        payload["position"] = [0, 0]
        payload["level"] = -1

        # When ready send it back to the server!
        await websocket.send(json.dumps(payload))
        print(f"Sending => {payload}")

        # Wait for the response/update and process it
        response = await websocket.recv()
        response = json.loads(response)
        print(f"Response => {response}")
        await asyncio.sleep(0.1)


async def main():
    """Typical client connection"""
    cache_data = await cache.load()

    # Temporary fix for the nickname
    if not cache_data["nickname"]:
        cache_data["nickname"] = input("Enter a nickname: ")

    async with websockets.connect("ws://localhost:8000/") as websocket:
        # Send the first data to initialize the connection
        payload = await hello(websocket, cache_data)
        # Now play the game
        await play(websocket, payload)


if __name__ == "__main__":
    asyncio.run(main())
