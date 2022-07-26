import asyncio
import json
import threading
from operator import itemgetter

import websockets

from .cache import CacheManager  # relative import otherwise it doesn't work

cache = CacheManager()
player_nickname = itemgetter("nickname")


class StoppableThread(threading.Thread):
    """
    Thread class with a stop() method.

    The thread itself has to check regularly for the stopped() condition.
    """

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        """Stop the running thread."""
        self._stop_event.set()

    def stopped(self):
        """Return is_set() response of thread."""
        return self._stop_event.is_set()


class Client:
    """Client class that handles the connection with the server."""

    def __init__(self, game):
        self.websocket = None
        self.broadcast = None
        self.game = game  # the game object is needed to check the player's position and level
        self.payload = {}
        self.unique_id = None

    async def _sync_engine(self):
        """Sync real game data to send back to the server!"""
        payload = {
            "type": "play",
            "position": list(self.game.player.rect.topleft),
            "level": -1,
            "direction": self.game.player.direction,
        }

        return payload

    async def _hello(self, cache_data):
        """Typical client/server hello connection"""
        no_cache = True if not all(cache_data.values()) else False

        hi = json.dumps(cache_data)
        await self.websocket.send(hi)
        print(f"Hello => {hi}")

        response = await self.websocket.recv()
        response = json.loads(response)
        print(f"Hello back => {response}")

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

            self.unique_id = cache_data["unique_id"]
            return cache_data
        else:
            raise Exception("Invalid type in response")

    async def _broadcast(self):
        """Listener for game broadcasts."""
        init = False
        # Wait for the response/update and process it
        async with websockets.connect("ws://134.255.220.44:8000/") as self.broadcast:
            while True:
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
                print(f"Public Broadcast => {response}")
                if response["type"] == "update":
                    await self._sync_players(response)
                elif response["type"] == "ping":
                    await self.broadcast.send(json.dumps({"type": "pong"}))

    async def _sync_players(self, response):
        """Update OtherPlayers from broadcasts!"""
        for player in response["players"]:
            nick = player_nickname(player)
            if nick == self.payload["nickname"]:
                continue
            if not any(ply for ply in self.game.other_players if ply.nickname == nick):
                self.game.add_player(nick, player["direction"], player["position"])
                continue
            self.game.update_player(nick, player["direction"], player["position"])

    async def _play(self, payload):
        """Play loop"""
        history = {"position": [0, 0], "level": -100}
        while True:
            payload = await self._sync_engine()
            self.payload.update(payload)

            # When moving & on spawn inform the server!
            if self.payload["position"] != history["position"] \
                or self.payload["level"] != history["level"]:
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

    async def _main(self):
        """Main client websocket"""
        cache_data = await cache.load()

        # TODO => Fix temp nickname
        if not cache_data["nickname"]:
            cache_data["nickname"] = input("Enter a nickname: ")

        async with websockets.connect("ws://134.255.220.44:8000/") as self.websocket:
            # Send the first data to initialize the connection
            self.payload = await self._hello(cache_data)
            # Now play the game
            await self._play(self.payload)

    def start(self):
        """Starts the listen/receive threads."""
        # The main thread.
        self.main_thread = StoppableThread(target=self._main_start, daemon=True)
        # Broadcast listener thread
        self.recv_thread = StoppableThread(target=self._recv_start, daemon=True)  # The connection thread.
        # We make it "daemon" so that the full process stops when the window is closed.
        # (If the thread is not daemon, we get a RuntimeError upon closing the window.)
        self.main_thread.start()
        self.recv_thread.start()

    def stop(self):
        """Stops the listen/receive threads."""
        self.main_thread.stop()
        self.recv_thread.stop()

    def _main_start(self):
        """Thread for receiving broadcasts."""
        asyncio.run(self._main())

    def _recv_start(self):
        """Main Thread, mostly for sending payloads to the server."""
        asyncio.run(self._broadcast())
