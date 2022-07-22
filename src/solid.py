import pygame


class Solid(pygame.sprite.Sprite):
    """The solid ground."""

    def __init__(self, tile_pos: tuple):
        """The solid ground.

        :param tile_pos: The tile's position. Represented as a tuple of integers (in tiles).
        """
        super().__init__()
        # tile_pos is a tuple of integers representing a tile's topleft corner coordinates
        self.tile_pos = tile_pos
        # We'll only need to multiply these coords by 16 to have the real position
        self.image = pygame.Surface((16, 16))
        self.image.fill("green")
        self.rect = self.image.get_rect(topleft=tuple(map(lambda x: x * 16, self.tile_pos)))
