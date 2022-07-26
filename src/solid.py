import pygame
import pathlib
import os.path as path
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


normal_gd = pygame.image.load(_resource_path("assets/tile.png")).convert_alpha()
upper_corner_r = pygame.image.load(_resource_path("assets/upper_corner.png")).convert_alpha()
upper_corner_l = pygame.transform.flip(upper_corner_r, True, False)
upper_corner_single = pygame.image.load(_resource_path("assets/upper_corner_single.png")).convert_alpha()
deep_gd = pygame.image.load(_resource_path("assets/deep_gd.png")).convert_alpha()
side_gd_r = pygame.image.load(_resource_path("assets/side_gd.png")).convert_alpha()
side_gd_l = pygame.transform.flip(side_gd_r, True, False)
side_gd_single = pygame.image.load(_resource_path("assets/side_gd_single.png")).convert_alpha()
side_end_r = pygame.image.load(_resource_path("assets/side_end.png")).convert_alpha()
side_end_l = pygame.transform.flip(side_end_r, True, False)
side_single = pygame.image.load(_resource_path("assets/side_single.png")).convert_alpha()
bottom_corner_r = pygame.image.load(_resource_path("assets/bottom_corner.png")).convert_alpha()
bottom_corner_l = pygame.transform.flip(bottom_corner_r, True, False)
bottom_corner_platform = pygame.image.load(_resource_path("assets/bottom_corner_platform.png")).convert_alpha()
single_gd = pygame.image.load(_resource_path("assets/single_gd.png")).convert_alpha()
bottom_corner_dual = pygame.image.load(_resource_path("assets/bottom_corner_dual.png")).convert_alpha()
bottom_corner_single = pygame.image.load(_resource_path("assets/bottom_corner_single.png")).convert_alpha()
bottom_gd = pygame.image.load(_resource_path("assets/bottom_gd.png")).convert_alpha()
inward_bottom_corner_r = pygame.image.load(_resource_path("assets/inward_bottom_corner.png")).convert_alpha()
inward_bottom_corner_l = pygame.transform.flip(inward_bottom_corner_r, True, False)
inward_bottom_corner_single = pygame.image.load(
    _resource_path("assets/inward_bottom_corner_single.png")
).convert_alpha()
inward_corner_r = pygame.image.load(_resource_path("assets/inward_corner.png")).convert_alpha()
inward_corner_l = pygame.transform.flip(inward_corner_r, True, False)
inward_corner_single = pygame.image.load(_resource_path("assets/inward_corner_single.png")).convert_alpha()
bricks = pygame.image.load(_resource_path("assets/bricks.png")).convert_alpha()
shiny_flag = _load_gif("assets/shiny_flag.gif")


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
        self.image = normal_gd
        self.rect = self.image.get_rect(topleft=tuple(map(lambda x: x * 16, self.tile_pos)))
        # Rectangles used for autotiling
        self.checks = (
            pygame.Rect(self.rect.x - 16, self.rect.y - 16, self.rect.width * 3, 16),  # top
            pygame.Rect(self.rect.x - 16, self.rect.bottom, self.rect.width * 3, 16),  # bottom
            pygame.Rect(self.rect.x - 16, self.rect.y - 16, 16, self.rect.height * 3),  # left
            pygame.Rect(self.rect.right, self.rect.y - 16, 16, self.rect.height * 3),
        )  # right

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
        self.image = pygame.image.load(_resource_path("assets/stone.png")).convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)


class Ending(pygame.sprite.Sprite):
    """Upon colliding with this sprite, the player will be teleported into the next level."""

    def __init__(self, tile_pos):
        super().__init__()
        self.tile_pos = tile_pos
        self.image = pygame.image.load(_resource_path("assets/end.png"))
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
        self.image = shiny_flag[self.frame - 1]
        self.frame_delay += dt
        if self.frame_delay >= 16:
            self.frame += 1
            if self.frame > len(shiny_flag):
                self.frame = 1
            self.frame_delay = 0
