import os.path as path
import pathlib

import pygame
import pytmx

import src.client.client as client
import src.player as player
import src.solid as solid
import src.gui as gui

pygame.mixer.init()

_resource_path = player._resource_path


game_crash = pygame.mixer.Sound(_resource_path("assets/game_crash.wav"))
game_crash.set_volume(0.35)  # We don't want players to get their eardrums destroyed


def complex_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t, _, _ = -l + 80, -t + 72, w, h  # center player

    l = min(0, l)  # stop scrolling at the left edge
    l = max(-(camera.width - 160), l)  # stop scrolling at the right edge
    t = max(-(camera.height - 144), t)  # stop scrolling at the bottom
    t = min(0, t)  # stop scrolling at the top

    return pygame.Rect(l, t, w, h)


class Camera(object):
    """Special camera object allowing us to keep the local player on-screen at all times no matter the level's size."""

    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = pygame.Rect(0, 0, width, height)

    def apply(self, target):
        """Return a copy of the target's rectangle which is positioned
        according to the current centered sprite."""
        return target.rect.move(self.state.topleft)

    def update(self, target):
        """Update the camera to follow a certain sprite for this frame."""
        self.state = self.camera_func(self.state, target.rect)

    def change_settings(self, width, height, x=0, y=0):
        """Change the size of the screen covered by the camera."""
        self.state.size = width, height
        self.state.topleft = x, y


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
        self.camera = Camera(complex_camera, 160, 144)
        self.gui = pygame.sprite.Group(gui.Button((80, 72), "Play", self.start))
        self.showing_gui = True
        self.read_map("maps/tutorial.tmx")  # we'll need to change that depending on the player's level

    def start(self):
        self.showing_gui = False
        self.client.start()

    def crash(self):
        """<<Crash>> the game."""
        self.crashing = True
        game_crash.play(-1)

    def read_map(self, directory):
        """This reads the TMX Map data"""
        # TMX is a variant of the XML format, used by the map editor Tiled.
        # Said maps use tilesets, stored in TSX files (which are also based on the XML format).
        self.tmx_data = pytmx.TiledMap(_resource_path(directory))
        self.camera.change_settings(self.tmx_data.width * 16, self.tmx_data.height * 16)
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
                    tile_id = tile["id"]
                    if tile_id not in [1, 20, 22]:
                        # Solid tile
                        new_spr = solid.Solid(self, (tile_x, tile_y), layer)
                        self._select_solid_image(new_spr, tile["type"], flipped_tile)
                        self.tiles.add(new_spr, layer=layer)
                    elif tile_id == 20:
                        # Level end tile.
                        pass
                    elif tile_id == 22:
                        # Shiny flag (tutorial tile)
                        self.tiles.add(solid.ShinyFlag((tile_x, tile_y)), layer=layer)
                    else:
                        # "Glitchy" tile (starts a pseudo-crash upon contact)
                        self.tiles.add(solid.BuggyThingy(self, (tile_x, tile_y), layer), layer=layer)
        for sprite in self.tiles:
            self.objects.add(sprite, layer=self.tiles.get_layer_of_sprite(sprite))

    def draw_objects(self, screen):
        """
        Replacement for self.objects.draw.

        Designed to take the camera into account.
        """
        self.camera.update(self.player)
        for layer in self.objects.layers():
            sprites = self.objects.get_sprites_from_layer(layer)
            for sprite in sprites:
                screen.blit(sprite.image, self.camera.apply(sprite))

    @staticmethod
    def _select_solid_image(tile, type, flipped):
        """
        Decide which image to use for this solid. * PRIVATE USE ONLY *

        :param tile: The solid tile impacted by this method.
        :param type: The solid's type, main image selection factor.
        :param flipped: This can change an image's orientation depending on whether this is true or false.
        """
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
            case 19:
                img = solid.bricks
            case 20:
                img = solid.shovel
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
        for ply in self.other_players:
            if ply.nickname not in active_nicknames:
                ply.kill()
