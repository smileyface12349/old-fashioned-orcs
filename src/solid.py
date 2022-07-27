import os.path as path
import pathlib

import pygame
from PIL import GifImagePlugin, ImageSequence


def _resource_path(file: str):
    """Return the absolute path for a file."""
    pathobj = pathlib.Path(file).absolute()
    return path.join(*pathobj.parts)


def _load_gif(file: str):
    """Load an animated GIF."""
    img = GifImagePlugin.GifImageFile(_resource_path(file))
    size = img.size
    first_frame = pygame.image.load(_resource_path(file)).convert_alpha()
    frames = [first_frame]
    for index, frame in enumerate(ImageSequence.Iterator(img)):
        if not index:
            continue
        data = frame.tobytes()
        frames.append(pygame.image.fromstring(data, size, img.mode).convert_alpha())
    return frames


def _load_img(file: str):
    """Load a normal image."""
    return pygame.image.load(_resource_path(file)).convert_alpha()


normal_gd = _load_img("assets/tile.png")
upper_corner_r = _load_img("assets/upper_corner.png")
upper_corner_l = pygame.transform.flip(upper_corner_r, True, False)
upper_corner_single = _load_img("assets/upper_corner_single.png")
deep_gd = _load_img("assets/deep_gd.png")
side_gd_r = _load_img("assets/side_gd.png")
side_gd_l = pygame.transform.flip(side_gd_r, True, False)
side_gd_single = _load_img("assets/side_gd_single.png")
side_end_r = _load_img("assets/side_end.png")
side_end_l = pygame.transform.flip(side_end_r, True, False)
side_single = _load_img("assets/side_single.png")
bottom_corner_r = _load_img("assets/bottom_corner.png")
bottom_corner_l = pygame.transform.flip(bottom_corner_r, True, False)
bottom_corner_platform = _load_img("assets/bottom_corner_platform.png")
single_gd = _load_img("assets/single_gd.png")
bottom_corner_dual = _load_img("assets/bottom_corner_dual.png")
bottom_corner_single = _load_img("assets/bottom_corner_single.png")
bottom_gd = _load_img("assets/bottom_gd.png")
inward_bottom_corner_r = _load_img("assets/inward_bottom_corner.png")
inward_bottom_corner_l = pygame.transform.flip(inward_bottom_corner_r, True, False)
inward_bottom_corner_single = _load_img("assets/inward_bottom_corner_single.png")
inward_corner_r = _load_img("assets/inward_corner.png")
inward_corner_l = pygame.transform.flip(inward_corner_r, True, False)
inward_corner_single = _load_img("assets/inward_corner_single.png")
bricks = _load_img("assets/bricks.png")
shiny_flag = _load_gif("assets/shiny_flag.gif")
shovel = _load_img("assets/shovel.png")
stone_block = _load_img("assets/stone_block.png")
cave_deep_gd = _load_img("assets/cave.png")
cave_bottom_gd = _load_img("assets/cave_bottom.png")
cave_bottom_corner_r = _load_img("assets/cave_bottom_corner.png")
cave_bottom_corner_l = pygame.transform.flip(cave_bottom_corner_r, True, False)
cave_bottom_corner_dual = _load_img("assets/cave_bottom_corner_dual.png")
cave_bottom_corner_single = _load_img("assets/cave_bottom_corner_single.png")
cave_inward_bottom_corner_r = _load_img("assets/cave_inward_bottom_corner.png")
cave_inward_bottom_corner_l = pygame.transform.flip(cave_inward_bottom_corner_r, True, False)
cave_inward_bottom_corner_single = _load_img("assets/cave_inward_bottom_corner_single.png")
cave_inward_corner_r = _load_img("assets/cave_inward_corner.png")
cave_inward_corner_l = pygame.transform.flip(cave_inward_corner_r, True, False)
cave_inward_corner_single = _load_img("assets/cave_inward_corner_single.png")
cave_side_gd_l = _load_img("assets/cave_left.png")
cave_side_gd_r = _load_img("assets/cave_right.png")
cave_side_end_r = _load_img("assets/cave_side_end.png")
cave_side_end_l = pygame.transform.flip(cave_side_end_r, True, False)
cave_side_single = _load_img("assets/cave_side_gd_single.png")
cave_side_gd_single = _load_img("assets/cave_side_single.png")
cave_single_gd = _load_img("assets/cave_single_gd.png")
cave_normal_gd = _load_img("assets/cave_top.png")
cave_upper_corner_r = _load_img("assets/cave_upper_corner.png")
cave_upper_corner_l = pygame.transform.flip(cave_upper_corner_r, True, False)
cave_upper_corner_single = _load_img("assets/cave_upper_corner_single.png")


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
        self._image = normal_gd
        self.rect = self.image.get_rect(topleft=tuple(map(lambda x: x * 16, self.tile_pos)))
        # Rectangles used for autotiling
        self.checks = (
            pygame.Rect(self.rect.x - 16, self.rect.y - 16, self.rect.width * 3, 16),  # top
            pygame.Rect(self.rect.x - 16, self.rect.bottom, self.rect.width * 3, 16),  # bottom
            pygame.Rect(self.rect.x - 16, self.rect.y - 16, 16, self.rect.height * 3),  # left
            pygame.Rect(self.rect.right, self.rect.y - 16, 16, self.rect.height * 3),
        )  # right

    @property
    def image(self):
        """Special property allowing for a dynamic collision mask update."""
        return self._image

    @image.setter
    def image(self, value):
        self._image = value
        self.mask = pygame.mask.from_surface(value)

    # Basic player-locating properties, used for collisions
    @property
    def playerisup(self):
        """Returns True if the player is above the Solid Tile, False otherwise."""
        return self.game.player.rect.bottom <= self.rect.y + 7

    @property
    def playerisdown(self):
        """Returns True if the player is below the Solid Tile, False otherwise."""
        return self.game.player.rect.y >= self.rect.bottom - 7

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
        self.image = _load_img("assets/stone.png")
        self.mask = pygame.mask.from_surface(self.image)


class Ending(pygame.sprite.Sprite):
    """Upon colliding with this sprite, the player will be teleported into the next level."""

    def __init__(self, tile_pos):
        super().__init__()
        self.tile_pos = tile_pos
        self.image = _load_img("assets/end.png")
        self.rect = self.image.get_rect(topleft=tuple(item * 16 for item in self.tile_pos))
        self.mask = pygame.mask.from_surface(self.image)


class ShinyFlag(pygame.sprite.Sprite):
    """A shiny flag"""

    def __init__(self, tile_pos):
        super().__init__()
        self.tile_pos = tile_pos
        self.frame = 1
        self.frame_delay = 0
        self.image = shiny_flag[self.frame - 1]
        self.rect = self.image.get_rect(topleft=tuple(item * 16 for item in self.tile_pos))

    def update(self, dt):
        """Update the Shiny flag"""
        self.image = shiny_flag[self.frame - 1]
        self.frame_delay += dt
        if self.frame_delay >= 36:
            self.frame += 1
            if self.frame > len(shiny_flag):
                self.frame = 1
            self.frame_delay = 0
