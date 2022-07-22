import pygame


class Solid(pygame.sprite.Sprite):
    """The solid ground."""

    def __init__(self, game, tile_pos: tuple):
        """The solid ground.

        :param tile_pos: The tile's position. Represented as a tuple of integers (in tiles).
        """
        super().__init__()
        # Once again the game object is needed for collisions
        self.game = game
        # tile_pos is a tuple of integers representing a tile's topleft corner coordinates
        self.tile_pos = tile_pos
        # We'll only need to multiply these coords by 16 to have the real position
        self.image = pygame.Surface((16, 16))
        self.image.fill("green")
        self.rect = self.image.get_rect(topleft=tuple(map(lambda x: x * 16, self.tile_pos)))
        print(self.rect)

    # Basic player-locating properties, used for collisions
    @property
    def playerisup(self):
        return self.game.player.rect.bottom <= self.rect.y + 6

    @property
    def playerisdown(self):
        return self.game.player.rect.y >= self.rect.bottom - 6

    @property
    def playerisleft(self):
        return self.game.player.rect.right <= self.rect.x + 2

    @property
    def playerisright(self):
        return self.game.player.rect.x >= self.rect.right - 2

    # Strict locating properties
    @property
    def playerisup_strict(self):
        return self.playerisup and not (self.playerisleft or self.playerisright)

    @property
    def playerisdown_strict(self):
        return self.playerisdown and not (self.playerisleft or self.playerisright)

    @property
    def playerisleft_strict(self):
        return self.playerisleft and not (self.playerisup or self.playerisdown)

    @property
    def playerisright_strict(self):
        return self.playerisright and not (self.playerisup or self.playerisdown)
