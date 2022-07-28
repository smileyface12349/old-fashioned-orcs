import asyncio
import json
import logging
import time

import websockets
from database import GameDatabase
from instances import GameManager, PlayerSession
from manager import ConnectionManager

logging.basicConfig(format="%(asctime)s - %(filename)s - %(message)s", level=logging.INFO)

games = GameManager()
manager = ConnectionManager()
db = GameDatabase()
players = set()


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
    joined = False
    for game in games.active_games:
        if len(game.players) <= 4:
            try:
                await game.add_player(player)
                await asyncio.sleep(1)
                await broadcast_update(game)
                joined = True
                await play_game(player, game)
            except KeyError as e:
                logging.info(e)
                continue
    if not joined:
        await new_game(player)


async def ping_pong(websocket):
    """Trying to keep broadcast alive."""
    while websocket:
        t0 = time.perf_counter()
        pong_waiter = await websocket.ping()
        await pong_waiter
        t1 = time.perf_counter()
        latency = f"{t1-t0:.2f}"
        message = json.dumps({"type": "ping", "latency": latency})
        await websocket.send(message)
        await asyncio.sleep(1)


async def broadcast_update(game):
    """Send an "update" event to everyone in the current game."""
    event = {"type": "update", "game_id": game.id, "players": [p.data() for p in game.players]}
    players = [p.broadcast for p in game.iter_players() if p.broadcast is not None]
    websockets.broadcast(players, json.dumps(event))


async def play_game(player, game):
    """Receive and process moves from players."""
    logging.info(f"Player {player.nickname} joined a game.")
    async for message in player.websocket:
        # Parse a "play" event from the client.
        event = json.loads(message)
        if event["type"] == "play":
            assert event["unique_id"] == player.unique_id
            await player.websocket.send(json.dumps(event))

            player.position = event["position"]
            player.level = event["level"]
            player.direction = event["direction"]
            request_id = event["unique_id"]

            event = {"type": "update", "game_id": game.id, "players": [p.data() for p in game.players]}
            # Send the "update" event to everyone in the current game but exclude the current player!
            other_players = [
                p.broadcast
                for p in game.iter_players()
                if p.unique_id != request_id and p.broadcast is not None and p.level == player.level
            ]
            websockets.broadcast(other_players, json.dumps(event))
        elif event["type"] == "exit":
            logging.info(f"Player {player.nickname} left.")


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
        player = None
        logging.info(f"New WebSocket => {websocket.remote_address}")
        event = await websocket.recv()
        event = json.loads(event)

        # Check if websocket is main or broadcast.
        if event["type"] in ["init", "ready", "play"]:

            if event["type"] in ["init", "ready"]:
                event = await manager.update(event)
                assert event["unique_id"]
                await manager.add_main(websocket)
                player.level = await db.load(event["unique_id"])
                event["level"] = player.level
                await websocket.send(json.dumps(event))

            # Create new player session
            player = PlayerSession(websocket, event["unique_id"], event["nickname"])
            players.add(player)
            # Load progress of player, if any

            if not games.active_games:
                # Start a new game.
                logging.info("Creating New Game!")
                await new_game(player)
            else:
                logging.info("Player will join an existing game!")
                await join_game(player)

        elif event["type"] == "broadcast":
            await manager.add_broadcast(websocket)
            for play in players:
                if play.unique_id == event["unique_id"]:
                    if not play.broadcast:
                        play.attach_broadcast(websocket)
                    break

            await websocket.send(json.dumps({"type": "broadcast"}))
            await ping_pong(websocket)

    except websockets.exceptions.ConnectionClosedError:
        logging.info(f"ConnectionClosedError from => {websocket.remote_address}")

    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"ConnectionClosedOK from => {websocket.remote_address}")

    finally:
        # Drop websocket after figuring out its type
        if websocket in manager.active_broadcasts:
            await manager.drop_broadcast(websocket)
            try:
                for play in players:
                    if play.unique_id == event["unique_id"]:
                        players.remove(play)
            except RuntimeError:
                pass
            logging.info(f"Closed game broadcast socket from => {websocket.remote_address}")
        elif websocket in manager.active_connections and player:
            await db.save(player)
            await games.remove_player(player)
            await games.clear()
            await manager.drop_main(websocket)
            logging.info(f"Closed main socket from => {websocket.remote_address}")


async def main():
    """Main function that starts the server."""
    async with websockets.serve(handler, "134.255.220.44", 8001, ping_interval=None, close_timeout=1):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
