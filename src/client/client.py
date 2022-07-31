import asyncio
import json
import os.path as path
import pathlib
import socket
import ssl
import threading
from asyncio.exceptions import CancelledError, IncompleteReadError
from operator import itemgetter

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from .cache import CacheManager  # relative import otherwise it doesn't work


def _resource_path(file: str):
    """Return the absolute path for a file."""
    pathobj = pathlib.Path(file).absolute()
    return path.join(*pathobj.parts)


ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations(_resource_path("assets/cert.pem"))
cache = CacheManager()
player_nickname = itemgetter("nickname")
player_level = itemgetter("level")


class Client:
    """Client class that handles the connection with the server."""

    def __init__(self, game):
        self.websocket = None
        self.broadcast = None
        self.game = game
        self.payload = {}
        self.unique_id = None
        self.running = False

    async def _sync_engine(self):
        """Sync real game data to send back to the server!"""
        data = {
            "type": "play",
            "position": list(self.game.player.rect.topleft),
            "level": self.game.level,
            "direction": self.game.player.direction,
        }
        return data

    async def _hello(self, cache_data):
        """Typical client/server hello connection"""
        no_cache = True if not all(cache_data.values()) else False

        hi = json.dumps(cache_data)
        await self.websocket.send(hi)
        print(f"Client hello => {hi}")

        response = await self.websocket.recv()
        response = json.loads(response)
        print(f"Server hello => {response}")

        if response["type"] in ["init", "ready"]:
            self.game.nickname = response["nickname"]

            if not cache_data["unique_id"]:
                # If user didnt have a unique_id, server returned him one
                cache_data["unique_id"] = response["unique_id"]

            if not cache_data["nickname"]:
                cache_data["nickname"] = self.game.nickname

            if no_cache:
                # If there is no cache saved, we need to create it
                await cache.save(response)
                no_cache = False
            if response["level"]:
                self.game.level = response["level"]
            else:
                self.game.level = 0
            self.game.read_map(f"maps/level{self.game.level}.tmx")
            self.unique_id = cache_data["unique_id"]
            return cache_data

    async def _broadcast(self):
        """Listener for game broadcasts."""
        init = False
        # Wait for the response/update and process it
        try:
            async with websockets.connect(
                "wss://oldfashionedorcs.servegame.com:8001/", close_timeout=1, ssl=ssl_context
            ) as self.broadcast:
                while self.running:
                    # Make sure main thread actually initialized
                    if not self.unique_id:
                        await asyncio.sleep(0.1)
                        continue
                    # First payload on this websocket needs to include unique_id
                    # So that the server can identify it and assign the socket to the same player
                    if not init:
                        await self.broadcast.send(json.dumps({"type": "broadcast", "unique_id": self.unique_id}))
                        init = True
                    # Now that we have initiliased, wait for actual updates/pings!
                    response = await self.broadcast.recv()
                    response = json.loads(response)
                    if response["type"] == "update":
                        print(f"Public Broadcast => {response}")
                        await self._sync_players(response)
                    elif response["type"] == "ping":
                        print(f"Private Ping Broadcast => {response}")
        except socket.gaierror:
            self.running = False
            print("Cannot connect to server. Try again later!")
        except ConnectionClosedOK:
            self.running = False
            print("Server closed your connection.")

    async def _sync_players(self, response):
        """Update OtherPlayers from broadcasts!"""
        nicknames = []
        for player in response["players"]:
            nick = player_nickname(player)
            level = player_level(player)
            nicknames.append(nick)
            if nick == self.payload["nickname"] or level != self.payload["level"]:
                continue
            if not any(ply for ply in self.game.other_players if ply.nickname == nick):
                self.game.add_player(nick, player["direction"], player["position"])
                continue
            self.game.update_player(nick, player["direction"], player["position"])
        self.game.check_who_left(nicknames)

    async def _play(self, data):
        """Play loop"""
        history = {"position": [0, 0], "level": -100}
        while self.running:
            data = await self._sync_engine()
            self.payload.update(data)

            # When moving & on spawn inform the server!
            if self.payload["position"] != history["position"] or self.payload["level"] != history["level"]:
                # Update history dict
                history["position"] = self.payload["position"]
                history["level"] = self.payload["level"]
                # Send the payload
                print(f"Payload => {self.payload}")
                await self.websocket.send(json.dumps(self.payload))
                # Wait for the check
                response = await self.websocket.recv()
                response = json.loads(response)
                print(f"Private Response => {response}")
        else:
            exit = json.dumps({"type": "exit"})
            await self.websocket.send(exit)
            await self.broadcast.send(exit)

    async def _main(self):
        """Main client websocket"""
        cache_data = await cache.load()
        cache_nick = player_nickname(cache_data)

        if not cache_nick:
            cache_data["nickname"] = self.game.nickname
        else:
            self.game.nickname = cache_nick
        del cache_nick

        try:
            async with websockets.connect(
                "wss://oldfashionedorcs.servegame.com:8001/", close_timeout=1, ssl=ssl_context
            ) as self.websocket:
                # Send the first data to initialize the connection
                self.payload = await self._hello(cache_data)
                # Now play the game
                self.payload["nickname"] = self.game.nickname
                await self._play(self.payload)
        except socket.gaierror:
            self.running = False
            print("Cannot connect to server. Try again later!")
        except ConnectionClosedOK:
            self.running = False
            print("Server closed your connection.")

    def start(self):
        """Starts the listen/receive threads."""
        # The main thread.
        self.main_thread = threading.Thread(target=self._main_start, daemon=True)
        # Broadcast listener thread
        self.recv_thread = threading.Thread(target=self._recv_start, daemon=True)
        # We make it "daemon" so that the full process stops when the window is closed.
        # (If the thread is not daemon, we get a RuntimeError upon closing the window.)
        self.main_thread.start()
        self.recv_thread.start()
        self.running = True

    def stop(self):
        """Stops the listen/receive threads."""
        self.running = False
        print("Exiting Recv Thread")
        self.recv_thread.join()
        print("Exiting Main Thread")
        self.main_thread.join()

    def _main_start(self):
        """Thread for receiving broadcasts."""
        try:
            asyncio.run(self._main())
        except TimeoutError or CancelledError:
            print("Cannot connect to server. Try again later!")
            self.running = False
        except ConnectionClosedError or IncompleteReadError:
            print("Connection closed.")
            self.running = False

    def _recv_start(self):
        """Main Thread, mostly for sending payloads to the server."""
        try:
            asyncio.run(self._broadcast())
        except TimeoutError or CancelledError:
            print("Cannot connect to server. Try again later!")
            self.running = False
        except ConnectionClosedError or IncompleteReadError:
            print("Connection closed.")
            self.running = False
