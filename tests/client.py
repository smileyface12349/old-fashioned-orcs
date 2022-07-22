import asyncio
import json
import websockets


async def test():
    """Just testing simple client connection"""
    uri = "ws://localhost:8000/connect"
    async with websockets.connect(uri) as websocket:

        payload = {"method": "test"}
        await websocket.send(json.dumps(payload))

        response = await websocket.recv()
        print(response)


if __name__ == "__main__":
    asyncio.run(test())
