import asyncio
import json
import logging

import websockets
from database import GameDatabase
from instances import GameManager, PlayerSession
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


async def new_game(player):
    """Handles a connection from the first player: start a new game."""
    game = await games.create()  # Initialize a game
    await game.add_player(player)

    # Receive and process moves from the first player.
    await play_game(player, game)


async def join_game(player):
    """Handle connections from other players, joining an existing game."""
    # Find the game.
    for game in games.active_games:
        if len(game.players) <= 2:
            try:
                await game.add_player(player)
                await play_game(player, game)

            except KeyError:
                await error(player.websocket, "Game not found.")
                await game.remove_player(player)
                return
        else:
            await new_game(player)


async def play_game(player, game):
    """Receive and process moves from players."""
    async for message in player.websocket:
        # Parse a "play" event from the client.
        event = json.loads(message)

        assert event["type"] == "play"
        assert event["unique_id"] == player.unique_id

        player.position = event["position"]
        player.level = event["level"]
        player.direction = event["direction"]

        # Send an "update" event back
        event = {"type": "update", "game_id": game.id, "players": [p.data() for p in game.players]}
        # Send the event to everyone after removing the id
        websockets.broadcast(game.iter_websockets(), json.dumps(event))


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
    try:
        logging.info(f"New WebSocket => {websocket.remote_address}")
        await manager.add(websocket)

        event = await manager.update(websocket)
        assert event["unique_id"]
        await websocket.send(json.dumps(event))

        # Clear old games if necessary
        await games.clear()
        # Create new player session
        player = PlayerSession(websocket, event["unique_id"], event["nickname"])
        # Load progress of player, if any
        player.level = await db.load(player)

        if not games.active_games:
            # Start a new game.
            logging.info("Creating New Game!")
            await new_game(player)
        else:
            logging.info("Player will join an existing game!")
            await join_game(player)

    except websockets.exceptions.ConnectionClosedError:
        logging.info(f"ConnectionClosedError on WebSocket => {websocket.remote_address}")

    finally:
        # Drop websocket when done
        await db.save(player)
        await manager.drop(websocket)
        await games.remove_player(player)
        logging.info(f"Closed WebSocket => {websocket.remote_address}")


async def main():
    """Main function that starts the server."""
    async with websockets.serve(handler, "localhost", 8000):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
