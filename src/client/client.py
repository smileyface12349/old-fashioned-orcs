import asyncio
import json
from operator import itemgetter

import websockets

from .cache import CacheManager  # relative import otherwise it doesn't work

cache = CacheManager()
player_nickname = itemgetter("nickname")


class Client:
    """Client class that handles the connection with the server."""

    def __init__(self, game):
        self.websocket = None
        self.game = game  # the game object is needed to check the player's position and level
        self.payload = {}

    def sync_game(self):
        """Sync real game data to send back to the server!"""
        payload = {"type": "play", "position": list(self.game.player.rect.topleft), "level": -1}
        return payload

    async def _hello(self, cache_data):
        """Typical client/server hello connection"""
        no_cache = True if not all(cache_data.values()) else False

        hi = json.dumps(cache_data)
        await self.websocket.send(hi)
        print(f"Sending => {hi}")

        response = await self.websocket.recv()
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

    async def play(self, payload):
        """Play loop"""
        print("=->  Playing  <-=")
        while True:
            loop = asyncio.get_event_loop()
            payload = await loop.run_in_executor(None, self.sync_game)
            self.payload.update(payload)

            # When ready send it back to the server!
            await self.websocket.send(json.dumps(self.payload))
            print(f"Sending => {self.payload}")

            # Wait for the response/update and process it
            response = await self.websocket.recv()
            response = json.loads(response)
            print(f"Response => {response}")
            for player in response["players"]:
                nick = player_nickname(player)
                if nick == self.payload["nickname"]:
                    continue
                if not any(ply for ply in self.game.other_players if ply.nickname == nick):
                    self.game.add_player(nick, player["position"])
                    continue
                self.game.update_player(nick, player["position"])
            await asyncio.sleep(0.025)

    async def run(self):
        """Typical client connection"""
        cache_data = await cache.load()

        # TODO => Fix temp nickname
        if not cache_data["nickname"]:
            cache_data["nickname"] = input("Enter a nickname: ")

        async with websockets.connect("ws://134.255.220.44:9876/") as self.websocket:
            # Send the first data to initialize the connection
            self.payload = await self._hello(cache_data)
            # Now play the game
            await self.play(self.payload)
