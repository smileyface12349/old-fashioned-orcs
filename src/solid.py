import pygame


class Solid(pygame.sprite.Sprite):
    """The solid ground."""

    def __init__(self, game, tile_pos: tuple, layer: int):
        """The solid ground.

        :param tile_pos: The tile's position. Represented as a tuple of integers (in tiles).
        """
        super().__init__()
        # Once again the game object is needed for collisions
        self.game = game
        self.layer = layer
        # tile_pos is a tuple of integers representing a tile's topleft corner coordinates
        self.tile_pos = tile_pos
        # We'll only need to multiply these coords by 16 to have the real position
        self.image = pygame.Surface((16, 16)).convert_alpha()
        self.image.fill("green")
        self.alphaing = False
        self.dealphaing = False
        self.alpha = 255
        self.alpha_delay = 0
        self.rect = self.image.get_rect(topleft=tuple(map(lambda x: x * 16, self.tile_pos)))

    def update(self, dt):
        if self.alphaing:
            self.alpha_delay += dt
            if self.alpha_delay >= 36:
                self.alpha -= 15
                self.alpha_delay = 0
                if self.alpha <= 125:
                    self.alphaing = False
        if self.dealphaing:
            self.alpha_delay += dt
            if self.alpha_delay >= 36:
                self.alpha_delay = 0
                self.alpha += 15
                if self.alpha == 255:
                    self.dealphaing = False
        if self.layer and pygame.sprite.spritecollide(self.game.player, [self], False):
            if not self.alphaing and self.alpha > 125:
                self.alphaing = True
                self.dealphaing = False
        else:
            if not self.dealphaing and self.alpha < 255:
                self.dealphaing = True
                self.alphaing = False
        self.image.set_alpha(self.alpha)

    # Basic player-locating properties, used for collisions
    @property
    def playerisup(self):
        """Returns True if the player is above the Solid Tile, False otherwise."""
        return self.game.player.rect.bottom <= self.rect.y + 6

    @property
    def playerisdown(self):
        """Returns True if the player is below the Solid Tile, False otherwise."""
        return self.game.player.rect.y >= self.rect.bottom - 6

    @property
    def playerisleft(self):
        """Returns True if the player is left of the Solid Tile, False otherwise."""
        return self.game.player.rect.right <= self.rect.x + 2

    @property
    def playerisright(self):
        """Returns True if the player is right of the Solid Tile, False otherwise."""
        return self.game.player.rect.x >= self.rect.right - 2

    # Strict locating properties
    @property
    def playerisup_strict(self):
        """Returns True if the player is directly above the Solid Tile, False otherwise."""
        return self.playerisup and not (self.playerisleft or self.playerisright)

    @property
    def playerisdown_strict(self):
        """Returns True if the player is directly below the Solid Tile, False otherwise."""
        return self.playerisdown and not (self.playerisleft or self.playerisright)

    @property
    def playerisleft_strict(self):
        """Returns True if the player is directly left of the Solid Tile, False otherwise."""
        return self.playerisleft and not (self.playerisup or self.playerisdown)

    @property
    def playerisright_strict(self):
        """Returns True if the player is right of left of the Solid Tile, False otherwise."""
        return self.playerisright and not (self.playerisup or self.playerisdown)


class BuggyThingy(Solid):
    """BuggyThingy class - Fix me"""

    def __init__(self, game, tile_pos: tuple, layer: int):
        super().__init__(game, tile_pos, layer)
        self.image.fill("red")
