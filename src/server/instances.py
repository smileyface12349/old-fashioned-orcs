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

    def players(self):
        """Returns a list of players"""
        return iter(self.players)


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

    async def clear(self):
        """Auto-checks for empty games."""
        for game in self.active_games:
            if len(game.players) == 0:
                self.active_games.remove(game)

    async def remove_player(self, player):
        """Remove player from its game"""
        for game in self.active_games:
            for local_player in game.players:
                if player == local_player:
                    await game.remove_player(player)

    def __iter__(self):
        """Iterates over active games."""
        return iter(self.active_games)

    def __call__(self):
        """Return a list of all currently active games."""
        return self.active_games
