import asyncio
import json
import logging

import websockets
from database import GameDatabase
from instances import GameManager
from manager import ConnectionManager

logging.basicConfig(format="%(asctime)s - %(filename)s - %(message)s", level=logging.INFO)

games = GameManager()
manager = ConnectionManager()
db = GameDatabase()


async def error(websocket, message):
    """Sends an error message over the socket."""
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))


async def new_game(websocket):
    """Handles a connection from the first player: start a new game."""
    game = await games.create()  # Initialize a game
    await game.add_player(websocket)

    # Receive and process moves from the first player.
    await play_game(websocket, game)


async def join_game(websocket):
    """Handle connections from other players, joining an existing game."""
    # Find the game.
    for game in games.active_games:
        if len(game.players) <= 2:
            try:
                await game.add_player(websocket)
                await play_game(websocket, game)

            except KeyError:
                await error(websocket, "Game not found.")
                await game.remove_player(websocket)
                return
        else:
            await new_game(websocket)


async def play_game(websocket, game):
    """Receive and process moves from players."""
    async for message in websocket:
        # Parse a "ready" event from the client.
        event = json.loads(message)
        assert event["type"] == "ready"

        try:
            # TODO => Actually play with the engine
            position = 0, 0
        except RuntimeError as e:
            # Send an "error" event if the move was illegal.
            await error(websocket, str(e))
            continue

        # Send an "action" event back
        event = {
            "type": "action",
            "game_id": game.id,
            "position": position,
            "level": 0,
        }
        websockets.broadcast(game.players, json.dumps(event))


async def handler(websocket):
    """
    This endpoint will handle the session of a player.

    Example first JSON payload:
    {
        "type": "init",
        "unique_id": "",
        "nickname": "coolnickname"
    }
    :param payload: json object
    """
    logging.info(f"New WebSocket => {websocket.remote_address}")
    await manager.add(websocket)

    event = await manager.update(websocket)
    assert event["unique_id"]
    await websocket.send(json.dumps(event))

    # Clear old games if necessary
    await games.clear()

    if not games.active_games:
        # Start a new game.
        logging.info("Creating New Game!")
        await new_game(websocket)
    else:
        logging.info("Player will join an existing game!")
        await join_game(websocket)

    # Drop websocket when done
    await manager.drop(websocket)
    await games.remove_player(websocket)
    logging.info(f"Closed WebSocket => {websocket.remote_address}")


async def main():
    """Main function that starts the server."""
    async with websockets.serve(handler, "localhost", 8000):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
