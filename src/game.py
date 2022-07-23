import os.path as path
import pathlib

import pygame
import pytmx

import src.player as player
import src.solid as solid

pygame.mixer.init()


def _resource_path(file: str):
    """Return the absolute path for a file."""
    pathobj = pathlib.Path(file).absolute()
    return path.join(*pathobj.parts)


game_crash = pygame.mixer.Sound(_resource_path("assets/game_crash.wav"))
game_crash.set_volume(0.5)  # We don't want players to get their eardrums destroyed


class Game:
    """The Game"""

    def __init__(self):
        self.player = player.Player(self)
        self.tiles = pygame.sprite.LayeredUpdates(
            solid.Solid(self, (5, 6)),
            solid.Solid(self, (4, 7)),
            solid.Solid(self, (6, 7)),
            solid.Solid(self, (5, 3)),
            default_layer=0,
        )
        self.objects = pygame.sprite.LayeredUpdates(self.player, *self.tiles)
        self.tmx_data: pytmx.TiledMap | None = None

    def read_map(self, directory):
        """This reads the TMX Map data"""
        # TMX is a variant of the XML format, used by the map editor Tiled.
        # Said maps use tilesets, stored in TSX files (which are also based on the XML format).
        self.tmx_data = pytmx.TiledMap(_resource_path(directory))
        for sprite in self.tiles:
            sprite.kill()
        tile_x = 0
        tile_y = 0
        for i, layer in enumerate(
            filter(lambda layers: isinstance(layers, pytmx.TiledTileLayer), self.tmx_data.layers)
        ):
            for row in layer.data:
                if not any(row):
                    tile_y += 1
                    tile_x = 0
                    continue
                for tile in row:
                    # A value of 0 means that the tile is empty.
                    if tile == 1:
                        # Solid tile
                        self.tiles.add(solid.Solid(self, (tile_x, tile_y)), layer=i)
                    elif tile == 2:
                        # "Glitchy" tile (starts a pseudo-crash upon contact)
                        # TODO: implement these.
                        pass
                    tile_x += 1
                tile_y += 1
                tile_x = 0
