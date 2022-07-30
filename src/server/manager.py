import random
import uuid

from websockets.legacy.server import WebSocketServerProtocol


class ConnectionManager:
    """It handles ALL players websockets"""

    def __init__(self):
        self.active_connections: set[WebSocketServerProtocol] = set()
        self.active_broadcasts: set[WebSocketServerProtocol] = set()
        self.active_nicknames = []

    async def add_main(self, websocket: WebSocketServerProtocol):
        """Accepts a new Player's websocket and adds it to the list."""
        self.active_connections.add(websocket)

    async def drop_main(self, websocket: WebSocketServerProtocol):
        """Handles proper disconnect of a Player and removes websocket from the list."""
        self.active_connections.remove(websocket)

    async def add_broadcast(self, websocket: WebSocketServerProtocol):
        """Accepts a new Player's websocket and adds it to the list."""
        self.active_broadcasts.add(websocket)

    async def drop_broadcast(self, websocket: WebSocketServerProtocol):
        """Handles proper disconnect of a Player and removes websocket from the list."""
        self.active_broadcasts.remove(websocket)

    async def update(self, payload):
        """Receives JSON payload from a websocket and updates client's unique_id if required."""
        if not self._is_valid(payload["unique_id"]):
            # Generate client's unique ID
            payload["unique_id"] = uuid.uuid4().hex
        if not payload["nickname"] or len(payload["nickname"]) > 12:
            # If a nickname wasnt given, generate a random one
            while True:
                payload["nickname"] = f"Guest{random.randint(1000, 2000)}"
                if payload["nickname"] not in self.active_nicknames:
                    self.active_nicknames.append(payload["nickname"])
                    break
        elif payload["nickname"] not in self.active_nicknames:
            self.active_nicknames.append(payload["nickname"])
        else:
            while True:
                payload["nickname"] += str(random.randint(1, 10))
                if payload["nickname"] not in self.active_nicknames:
                    self.active_nicknames.append(payload["nickname"])
                    break
        return payload

    def _is_valid(self, uuid_to_test):
        """Checks validity of the uuid hex."""
        try:
            uuid.UUID(str(uuid_to_test))
            return True
        except ValueError:
            return False

    def connections(self):
        """Return a list of all currently active connections."""
        return iter(self.active_connections)

    def broadcasts(self):
        """Return a list of all currently active connections."""
        return iter(self.active_broadcasts)
