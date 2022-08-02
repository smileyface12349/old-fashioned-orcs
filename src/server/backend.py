import asyncio
import json
import logging
import os.path as path
import pathlib
import ssl
import time

import websockets
from anticheat import GameAntiCheat
from database import GameDatabase
from instances import GameManager, PlayerSession
from manager import ConnectionManager


def _resource_path(file: str):
    """Return the absolute path for a file."""
    pathobj = pathlib.Path(file).absolute()
    return path.join(*pathobj.parts)


ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(_resource_path("server-cert.pem"), keyfile=_resource_path("server-key.pem"))
logging.basicConfig(format="%(asctime)s - %(filename)s - %(message)s", level=logging.INFO)

games = GameManager()
manager = ConnectionManager()
db = GameDatabase()
anticheat = GameAntiCheat()


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
        if not len(game.players) >= 2:
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


async def join_with_code(player, code):
    """Handle connections from other players, joining an existing game."""
    # Find the game.
    joined = False
    for game in games.active_games:
        if game.join_pin == code:
            logging.info(f"Player joined using code: {code}")
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
        logging.info(f"Player tried to use code: {code} but failed.")
        await new_game(player)


async def ping_pong(websocket):
    """Trying to keep broadcast alive."""
    while websocket in manager.active_broadcasts:
        t0 = time.perf_counter()
        pong_waiter = await websocket.ping()
        await pong_waiter
        t1 = time.perf_counter()
        latency = f"{t1-t0:.2f}"
        message = json.dumps({"type": "ping", "latency": latency})
        await websocket.send(message)
        await asyncio.sleep(0.5)


async def broadcast_update(game):
    """Send an "update" event to everyone in the current game."""
    event = {"type": "update", "game_id": game.id, "players": [p.data() for p in game.players]}
    _players = [p.broadcast for p in game.iter_players() if p.broadcast is not None]
    websockets.broadcast(_players, json.dumps(event))


async def play_game(player, game):
    """Receive and process moves from players."""
    logging.info(f"Player {player.nickname} joined a game.")
    async for message in player.websocket:
        # Parse a "play" event from the client.
        event = json.loads(message)
        if event["type"] == "play":

            # So before echoing back the payload and
            # actually update the logical PlayerSession, anticheat will check the event.
            player.banned = await anticheat.ensure(event, player, game)
            if player.banned:
                logging.info(f"Player {player.nickname} got banned.")
                await close_broadcast(player.broadcast, event["unique_id"])
                break

            # Echo the payload back to let client know we got it but add the pin_code for the game.
            event["pin_code"] = game.join_pin
            await player.websocket.send(json.dumps(event))

            # Now that we trust the event, we update the server from the event
            player.position = event["position"]
            if player.level != event["level"]:
                player.level = event["level"]
                await broadcast_update(game)
            player.direction = event["direction"]
            request_id = event["unique_id"]

            event = {"type": "update", "game_id": game.id, "players": [p.data() for p in game.players]}
            # Send the "update" event to everyone in the current level but exclude the current player!
            other_players = [
                p.broadcast
                for p in game.iter_players()
                if p.unique_id != request_id and p.broadcast is not None and p.level == player.level
            ]
            websockets.broadcast(other_players, json.dumps(event))
        elif event["type"] == "exit":
            logging.info(f"Player {player.nickname} left.")
            await close_broadcast(player.broadcast, request_id)


async def close_main(websocket, player):
    """Close main websocket properly."""
    logging.info(f"Closed main socket of => {player.nickname}")
    manager.active_nicknames.remove(player.nickname)
    await db.save(player)
    await games.remove_player(player)
    await games.clear()
    await manager.drop_main(websocket)


players = set()


async def close_broadcast(websocket, request_id):
    """Close broadcast websocket properly."""
    for play in players.copy():
        if play.unique_id == request_id:
            players.remove(play)
            logging.info(f"Closed game broadcast of => {play.nickname}")
    await manager.drop_broadcast(websocket)


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
        if event["type"] in ["init", "ready"]:
            event = await manager.update(event)
            assert event["unique_id"]
            await manager.add_main(websocket)
            # Create new player session
            player = PlayerSession(websocket, event["unique_id"], event["nickname"])
            players.add(player)
            # Load progress of player, if any
            player.level = await db.load(event["unique_id"])
            event["level"] = player.level if player.level else 0
            await websocket.send(json.dumps(event))

            await games.clear()
            if not games.active_games:
                # Start a new game.
                logging.info("Creating New Game!")
                await new_game(player)
            elif games.active_games and event["pin_code"]:
                await join_with_code(player, event["pin_code"])
            else:
                logging.info("Player will join a random existing game!")
                await join_game(player)

        elif event["type"] == "broadcast":
            await websocket.send(json.dumps({"type": "broadcast"}))
            await manager.add_broadcast(websocket)
            for play in players.copy():
                if play.unique_id == event["unique_id"]:
                    while True:
                        if isinstance(websocket, websockets.legacy.server.WebSocketServerProtocol):
                            logging.info("Attached websocket")
                            play.attach_broadcast(websocket)
                            await ping_pong(websocket)
                            break
                        else:
                            await asyncio.sleep(0.2)

    except websockets.exceptions.ConnectionClosedError:
        logging.info("Websocket closed with ConnectionClosedError")

    except websockets.exceptions.ConnectionClosedOK:
        logging.info("Websocket closed with ConnectionClosedOK")

    finally:
        # Drop websocket after figuring out its type
        if websocket in manager.active_connections and player:
            await close_main(websocket, player)
        elif websocket in manager.active_broadcasts:
            await close_broadcast(websocket, event["unique_id"])


async def main():
    """Main function that starts the server."""
    async with websockets.serve(handler, "0.0.0.0", 8000, ssl=ssl_context, ping_interval=None, close_timeout=1):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
