import os.path as path
import pathlib

import pygame
import pytmx

import src.client.client as client
import src.player as player
import src.solid as solid

pygame.mixer.init()

_resource_path = player._resource_path


game_crash = pygame.mixer.Sound(_resource_path("assets/game_crash.wav"))
game_crash.set_volume(0.35)  # We don't want players to get their eardrums destroyed


class Game:
    """The Game"""

    def __init__(self):
        self.player = player.Player(self)
        self.tiles = pygame.sprite.LayeredUpdates()
        self.other_players = pygame.sprite.Group()
        self.objects = pygame.sprite.LayeredUpdates(self.player)
        self.crashing = False
        self.tmx_data: pytmx.TiledMap | None = None
        self.client = client.Client(self)
        self.level = -1  # Value for the test map.
        self.read_map("maps/test.tmx")

    def crash(self):
        """<<Crash>> the game."""
        self.crashing = True
        game_crash.play(-1)

    def read_map(self, directory):
        """This reads the TMX Map data"""
        # TMX is a variant of the XML format, used by the map editor Tiled.
        # Said maps use tilesets, stored in TSX files (which are also based on the XML format).
        self.tmx_data = pytmx.TiledMap(_resource_path(directory))
        for sprite in self.tiles:
            sprite.kill()
        with open(_resource_path(directory)) as file:
            content = file.read()
        for layer in range(len(list(self.tmx_data.visible_tile_layers))):
            raw_tile_layer = list(
                map(
                    lambda string: string.split(",")[:-1] if string.count(",") == 16 else string.split(","),
                    content.split("""<data encoding="csv">""")[1 + layer].split("</data>")[0].splitlines(),
                )
            )[1:]
            for tile_y in range(self.tmx_data.height):
                for tile_x in range(self.tmx_data.width):
                    gid = int(raw_tile_layer[tile_y][tile_x])
                    flipped_tile = gid & 0x80000000
                    tile = self.tmx_data.get_tile_properties(tile_x, tile_y, layer)
                    if tile is None:
                        continue
                    if tile["id"] != 1:
                        # Solid tile
                        new_spr = solid.Solid(self, (tile_x, tile_y), layer)
                        self._select_solid_image(new_spr, tile["type"], flipped_tile)
                        self.tiles.add(new_spr, layer=layer)
                    else:
                        # "Glitchy" tile (starts a pseudo-crash upon contact)
                        self.tiles.add(solid.BuggyThingy(self, (tile_x, tile_y), layer), layer=layer)
        for sprite in self.tiles:
            self.objects.add(sprite, layer=self.tiles.get_layer_of_sprite(sprite))

    @staticmethod
    def _select_solid_image(tile, type, flipped):
        """Decide which image to use for this solid.
        PRIVATE USE ONLY

        :param tile: The solid tile impacted by this method.
        :param type: The solid's type, main image selection factor.
        :param flipped: This can change an image's orientation depending on whether this is true or false."""
        # We might have to extend that in the future when we encounter more tiling situations.
        match type:
            case 0 | 13:
                img = solid.normal_gd
            case 1:
                img = solid.bottom_corner_r if not flipped else solid.bottom_corner_l
            case 2:
                img = solid.bottom_corner_dual
            case 3:
                img = solid.bottom_corner_single
            case 4:
                img = solid.bottom_gd
            case 5:
                img = solid.deep_gd
            case 6:
                img = solid.inward_bottom_corner_r if not flipped else solid.inward_bottom_corner_l
            case 7:
                img = solid.inward_bottom_corner_single
            case 8:
                img = solid.inward_corner_r if not flipped else solid.inward_corner_l
            case 9:
                img = solid.inward_corner_single
            case 10:
                img = solid.side_gd_r if not flipped else solid.side_gd_l
            case 11:
                img = solid.side_gd_single
            case 12:
                img = solid.single_gd
            case 14:
                img = solid.upper_corner_r if not flipped else solid.upper_corner_l
            case 15:
                img = solid.upper_corner_single
            case 16:
                img = solid.side_end_r if not flipped else solid.side_end_l
            case 17:
                img = solid.side_single
            case 18:
                img = solid.bottom_corner_platform
        tile.image = img

    def add_player(self, nickname, direction, pos=None):
        """Adds a player that joined the game online."""
        if pos is None:
            pos = [0, 0]
        new_player = player.OtherPlayer(nickname, direction)
        self.other_players.add(new_player)
        self.objects.add(new_player, layer=0)
        new_player.rect.topleft = tuple(pos)

    def update_player(self, nickname, direction, pos=None):
        """Update players movement"""
        if pos is None:
            pos = [0, 0]
        if not any(other_player for other_player in self.other_players if other_player.nickname == nickname):
            raise Exception(f"invalid player : {nickname}")
        for other_player in self.other_players:
            if other_player.nickname == nickname:
                other_player.rect.topleft = tuple(pos)
                other_player.direction = direction

    def check_who_left(self, active_nicknames):
        """Check who left!"""
        for player in self.other_players:
            if player.nickname not in active_nicknames:
                player.kill()
