import os.path as path
import pathlib

import pygame
import pytmx

import src.player as player
import src.solid as solid


def _get_tmx_file(tmx: str):
    """Return the absolute path for a TMX map data."""
    pathobj = pathlib.Path(tmx).absolute()
    return path.join(*pathobj.parts)


class Game:
    """The Game"""

    def __init__(self):
        self.player = player.Player()
        self.tiles = pygame.sprite.LayeredUpdates(solid.Solid((8, 10)), default_layer=0)
        self.objects = pygame.sprite.LayeredUpdates(self.player, *self.tiles)

    def read_map(self, directory):
        """This reads the TMX Map data"""
        self.tmx_data = pytmx.TiledMap(_get_tmx_file(directory))
