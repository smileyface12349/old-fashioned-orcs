import uuid


class GameInstance:
    """Logical Game Instance"""

    def __init__(self, game_id):
        self.id = game_id
        self.players = []

    def id(self):
        """Returns Game's unique id."""
        return self.id

    async def add_player(self, player):
        """Add a player to an existing game"""
        self.players.append(player)

    async def remove_player(self, player):
        """Remove player from an existing game"""
        self.players.remove(player)

    async def players(self):
        """Returns a list of players"""
        return self.players


class GameManager:
    """It handles ALL logical game instances to enable multiplayer and keep track of players."""

    def __init__(self):
        self.active_games = []

    async def create(self):
        """Creates a logical new game."""
        game_id = uuid.uuid4().hex
        game = GameInstance(game_id)
        self.active_games.append(game)
        return game

    async def delete(self, game: GameInstance):
        """Deletes a game if no players in it."""
        del self.active_games.remove[game]

    def __iter__(self):
        """Return a list of all currently active games."""
        return iter(self.active_games)
