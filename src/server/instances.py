import logging
import uuid


class PlayerSession:
    """Logical Player to keep track of its data"""

    def __init__(self, websocket, unique_id, nickname):
        self.websocket = websocket
        self.broadcast = None
        self.unique_id = unique_id
        self.nickname = nickname
        self.banned = None
        self.violations = 0
        self.level = -1
        self.position = [0, 0]
        self.direction = "r"

    def data(self):
        """Returns all public data for a Player (position, nickname, level)"""
        return {"nickname": self.nickname, "position": self.position, "level": self.level, "direction": self.direction}

    def attach_broadcast(self, websocket):
        """Adds second websocket in Player"""
        self.broadcast = websocket


class GameInstance:
    """Logical Game Instance"""

    def __init__(self, game_id):
        self.id = game_id
        self.players = []
        self.sockets = []
        self.nicknames = []

    async def add_player(self, player):
        """Add a player to an existing game"""
        if player.nickname in self.nicknames:
            raise KeyError("Nickname in use")
        self.nicknames.append(player.nickname)
        self.players.append(player)
        self.sockets.append(player.websocket)

    async def remove_player(self, player):
        """Remove player from an existing game"""
        self.nicknames.remove(player.nickname)
        self.players.remove(player)
        self.sockets.remove(player.websocket)

    def iter_players(self):
        """Returns a list of players"""
        return iter(self.players)

    def iter_websockets(self):
        """Returns a list of players"""
        return iter(self.sockets)


class GameManager:
    """It handles ALL logical game instances to enable multiplayer and keep track of players."""

    def __init__(self):
        self.active_games = []

    async def create(self):
        """Creates a logical new game."""
        game_id = uuid.uuid4().hex
        new_game = GameInstance(game_id)
        self.active_games.append(new_game)
        logging.info(f"Created game with id: {new_game.id}")
        return new_game

    async def delete(self, game: GameInstance):
        """Deletes a game if no players in it."""
        del self.active_games.remove[game]

    async def clear(self):
        """Auto-checks for empty games."""
        for game in self.active_games:
            if len(game.players) == 0:
                logging.info(f"Deleting empty game with id: {game.id}")
                self.active_games.remove(game)

    async def remove_player(self, player):
        """Remove player from its game"""
        for game in self.active_games:
            for local_player in game.players:
                if player == local_player:
                    await game.remove_player(player)
                    from backend import broadcast_update

                    await broadcast_update(game)

    def __iter__(self):
        """Iterates over active games."""
        return iter(self.active_games)

    def __call__(self):
        """Return a list of all currently active games."""
        return self.active_games
