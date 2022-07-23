import asyncio
import json
import logging

import websockets
from database import GameDatabase
from manager import ConnectionManager

logging.basicConfig(format="%(asctime)s - %(filename)s - %(message)s", level=logging.INFO)

manager = ConnectionManager()
db = GameDatabase()


async def handler(websocket):
    """
    This endpoint will handle the session of a player.

    Example JSON payload:
    {
        "unique_id": "",
        "nickname": "coolname",
        "position_x": 150,
        "position_y": 350,
        "level": 1
    }
    :param payload: json object
    """
    logging.info(f"New WebSocket => {websocket.remote_address}")
    await manager.connect(websocket)

    # TODO => Interact with the game here using the payload & create the appropriate response

    response = await manager.update(websocket)
    await websocket.send(json.dumps(response))

    manager.disconnect(websocket)


async def main():
    """Main function that starts the server."""
    async with websockets.serve(handler, "localhost", 8000):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
