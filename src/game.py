import json
import os

import pygame
import pytmx

import src.client.client as client
import src.gui as gui
import src.player as player
import src.solid as solid

pygame.mixer.init()

_resource_path = player._resource_path

crash = pygame.image.load(_resource_path("assets/crash.png")).convert_alpha()
loading = pygame.image.load(_resource_path("assets/loading.png")).convert_alpha()
disconnected = pygame.image.load(_resource_path("assets/connection_lost.png")).convert_alpha()
title = solid._load_img("assets/title.png")
title_team = solid._load_img("assets/title_team.png")

mixer = pygame.mixer.music
mixer.set_volume(0.2)
mixer.load(_resource_path("assets/TheBuilder.mp3"))

game_crash = pygame.mixer.Sound(_resource_path("assets/game_crash.wav"))
game_crash.set_volume(0.2)


def complex_camera(camera, target_rect):
    """Compute Camera position."""
    l, t, _, _ = target_rect  # noqa: E741
    _, _, w, h = camera
    l, t, _, _ = -l + 80, -t + 72, w, h  # noqa: E741 # center player

    l = min(0, l)  # noqa: E741 # stop scrolling at the left edge
    l = max(-(camera.width - 160), l)  # noqa: E741 # stop scrolling at the right edge
    t = max(-(camera.height - 144), t)  # stop scrolling at the bottom
    t = min(0, t)  # stop scrolling at the top

    return pygame.Rect(l, t, w, h)


class Camera(object):
    """Special camera object allowing us to keep the local player on-screen at all times no matter the level's size."""

    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = pygame.Rect(0, 0, width, height)

    def apply(self, target):
        """Return a copy of the target's rectangle which is positioned according to the current centered sprite."""
        return target.rect.move(self.state.topleft)

    def update(self, target):
        """Update the camera to follow a certain sprite for this frame."""
        self.state = self.camera_func(self.state, target.rect)

    def change_settings(self, width, height, x=0, y=0):
        """Change the size of the screen covered by the camera."""
        self.state.size = width, height
        self.state.topleft = x, y


TYPE_MAPPINGS: dict[str, type] = {
    "flag": solid.ShinyFlag,
    "solid": solid.Solid,
    "npc1": solid.NPC,
    "blue_cube": solid.Ending,
    "button": solid.Switch,
}


class EventTrigger:
    """Event trigger object"""

    def __init__(self, mgr, id, arg_list):
        self.mgr = mgr
        self.game = mgr.game
        self.id = id
        self.arg_list = arg_list
        self._triggered = False
        self.trigger_duration_reached = False
        self.type = arg_list[0]
        if self.type == "and":
            self._evts = list(map(lambda tgr: EventTrigger(self.mgr, "", tgr), self.arg_list[1]))
        else:
            self._evts = None
        self.trigger_delay = 0
        self.has_credits = False
        self._required_evt = None
        self.dial_index = 0
        self.trigger_max = (
            self.arg_list[2] * 1000
        )  # we need to convert this in milliseconds so that events don't immediately happen
        try:
            self.dialogues = self.mgr.dialogues[self.id]
            if "require:" in self.dialogues[0]:
                self._required_evt = list(
                    trigger
                    for trigger in self.mgr.trigger_objs
                    if trigger.id == self.dialogues[0].removeprefix("require:")
                )[0]
                self.dialogues = self.dialogues[1:]
            if "credits" in self.dialogues:
                cred_pos = self.dialogues.index("credits")
                self.dialogues.pop(cred_pos)
                self.dialogues[
                    cred_pos : cred_pos + len(self.mgr.level_data["credits"]["dialogue"]["start"])
                ] = self.mgr.level_data["credits"]["dialogue"]["start"]
                self.has_credits = True
        except KeyError:
            self.dialogues = []

    def _set_triggered(self, val: bool):
        """Private setter for the triggered flag."""
        if self._evts is not None:
            for evt in self._evts:
                evt.triggered = val
        self._triggered = val

    triggered = property(lambda self: self._triggered, _set_triggered)

    def __repr__(self):
        return f"<EventTrigger(id='{self.id}', arg_list={self.arg_list}, triggered={self.triggered})>"

    def update_evt(self):
        """Update dialogue box with event"""
        if self.dial_index < len(self.dialogues):
            dial = self.dialogues[self.dial_index]
            if isinstance(dial, str):
                if dial == "title":
                    mixer.fadeout(2)
                    mixer.unload()
                    mixer.load(_resource_path("assets/epic.mp3"))
                    mixer.play(-1)
                if dial not in ["crash", "credits"]:
                    self.game.gui.add(gui.TextBox(self.game, dial))
                    self.dial_index += 1
                else:
                    if not self.game.crashing:
                        self.game.crash()
            else:
                if "despawn_layer" not in dial and "crash" not in dial:
                    char = dial["character"]
                    self.game.gui.add(
                        gui.TextBox(
                            self.game,
                            dial["text"],
                            f"[{char if char not in ('player', 'you') else self.game.nickname}]",
                        )
                    )
                    self.dial_index += 1
                elif "crash" in dial:
                    self.game.crash()
                else:
                    despawn_layer = self.game.tiles.get_sprites_from_layer(dial["despawn_layer"])
                    for spr in despawn_layer:
                        if spr.tile_pos == tuple(dial["coords"]):
                            spr.kill()
                            break
                    self.dial_index += 1
                    self.update_evt()
        else:
            self.mgr.current_trigger = None
            self.game.gui.empty()
            if self.has_credits:
                mixer.fadeout(3)
                self.game.showing_gui = True
                self.game.showing_title = True
                game_crash.stop()
                self.game.gui.add(gui.Button((48, 90), "Play", self.game.start))
                self.game.gui.add(gui.Button((110, 90), "Reset", self.game.del_cache))
                self.game.gui.add(gui.Button((80, 110), "Exit Game", self.game.quit))
                self.game.gui.add(gui.EmojiButton((148, 10), "♬", self.game.sound_on_off))
                self.game.level = 5
                self.game.client.stop()

    def update(self, dt):
        """Can be used in cases where the current trigger should be enabled after a certain period of time."""
        if self.trigger_max and self.trigger_condition():
            self.trigger_delay += dt
            if self.trigger_delay >= self.trigger_max:
                self.trigger_duration_reached = True
                self.trigger_delay = 0
        else:
            self.trigger_duration_reached = False
            self.trigger_delay = 0

    def can_be_triggered(self):
        """Check if the trigger can be enabled."""
        return (
            self.trigger_condition()
            if not self.trigger_max
            else self.trigger_condition() and self.trigger_duration_reached
        )

    def trigger_condition(self):
        """The trigger's main requirement. This does not rely on the maximum delay before enabling if there is one."""
        tiles_on_same_layer = self.game.tiles.get_sprites_from_layer(0)
        val = False
        match self.type:
            case "start":
                val = True
            case "touch_player":
                # Only happens when the LOCAL player meets the given requirements.
                if isinstance(self.arg_list[1], str):
                    val = bool(
                        pygame.sprite.spritecollide(
                            self.game.player,
                            tiles_on_same_layer if "button" not in self.arg_list[1] else self.game.tiles,
                            False,
                            lambda spr1, spr2: isinstance(spr2, TYPE_MAPPINGS[self.arg_list[1]])
                            and pygame.sprite.collide_mask(spr1, spr2),
                        )
                    )
                else:
                    val = bool(
                        pygame.sprite.spritecollide(
                            self.game.player,
                            tiles_on_same_layer if "button" not in self.arg_list[1][0] else self.game.tiles,
                            False,
                            lambda spr1, spr2: isinstance(spr2, TYPE_MAPPINGS[self.arg_list[1][0]])
                            and (
                                (spr2.tile_type == self.arg_list[1][1])
                                if self.arg_list[1][0] == "solid"
                                else (spr2.id == self.arg_list[1][1])
                            )
                            and pygame.sprite.collide_mask(spr1, spr2),
                        )
                    )
            case "touch":
                # Happens when ANY player (local or not) meets the given requirements.
                if isinstance(self.arg_list[1], str):
                    val = bool(
                        pygame.sprite.spritecollide(
                            self.game.player,
                            tiles_on_same_layer if "button" not in self.arg_list[1] else self.game.tiles,
                            False,
                            lambda spr1, spr2: isinstance(spr2, TYPE_MAPPINGS[self.arg_list[1]])
                            and pygame.sprite.collide_mask(spr1, spr2),
                        )
                    ) or bool(
                        pygame.sprite.groupcollide(
                            self.game.other_players,
                            tiles_on_same_layer if "button" not in self.arg_list[1] else self.game.tiles,
                            False,
                            False,
                            lambda spr1, spr2: isinstance(spr2, TYPE_MAPPINGS[self.arg_list[1]])
                            and pygame.sprite.collide_mask(spr1, spr2),
                        )
                    )
                else:
                    val = bool(
                        pygame.sprite.spritecollide(
                            self.game.player,
                            tiles_on_same_layer if "button" not in self.arg_list[1][0] else self.game.tiles,
                            False,
                            lambda spr1, spr2: isinstance(spr2, TYPE_MAPPINGS[self.arg_list[1][0]])
                            and (
                                (spr2.tile_type == self.arg_list[1][1])
                                if self.arg_list[1][0] == "solid"
                                else (spr2.id == self.arg_list[1][1])
                            )
                            and pygame.sprite.collide_mask(spr1, spr2),
                        )
                    ) or bool(
                        pygame.sprite.groupcollide(
                            self.game.other_players,
                            tiles_on_same_layer if "button" not in self.arg_list[1][0] else self.game.tiles,
                            False,
                            False,
                            lambda spr1, spr2: isinstance(spr2, TYPE_MAPPINGS[self.arg_list[1][0]])
                            and pygame.sprite.collide_mask(spr1, spr2)
                            and (
                                (spr2.tile_type == self.arg_list[1][1])
                                if self.arg_list[1][0] == "solid"
                                else (spr2.id == self.arg_list[1][1])
                            ),
                        )
                    )
            case "left":
                val = self.game.player.rect.x <= self.arg_list[1]
            case "right":
                val = self.game.player.rect.right >= self.arg_list[1]
            case "and":
                val = all(evt.trigger_condition() for evt in self._evts)
        return val and not self.triggered and (self._required_evt is None or self._required_evt.triggered)


class EventTriggerManager:
    """The event trigger manager."""

    def __init__(self, game):
        self.game = game
        with open(_resource_path("maps/levels.json"), "r", encoding="utf-8") as file:
            self.level_data = json.loads(file.read())
        self.triggers = {}
        self.dialogues = {}
        self.current_trigger: EventTrigger | None = None
        self.trigger_objs: list[EventTrigger] = []

    def check_triggers(self, dt):
        """Enable triggers if there are some."""
        if not self.current_trigger:
            for trigger in self.trigger_objs:
                trigger.update(dt)
                if trigger.can_be_triggered():
                    trigger.triggered = True
                    self.current_trigger = trigger
                    print(trigger)
                    for trgger in self.trigger_objs:
                        if trigger is trgger or not trgger.trigger_max:
                            continue
                        trgger.trigger_delay = 0
                    trigger.update_evt()
                    break

    def set_triggers(self, level: int | str):
        """Set up triggers for this level."""
        self.current_trigger = None
        self.trigger_objs.clear()
        self.triggers.clear()
        self.dialogues.clear()
        data = self.level_data[str(level)]
        self.triggers.update(data["events"])
        self.dialogues.update(data["dialogue"])
        for item in self.triggers.items():
            self.trigger_objs.append(EventTrigger(self, *item))
        print(self.trigger_objs)


class SwitchDestroyManager:
    """Used to despawn tiles when a switch is pressed."""

    def __init__(self, game):
        self.game = game
        self.objects = {}

    def destroy(self, switch: int):
        """Destroy all the tiles associated with this switch."""
        if switch in self.objects:
            for obj in self.objects[switch]:
                for tile in filter(lambda tile: tile.rect.colliderect(obj), self.game.tiles.get_sprites_from_layer(0)):
                    tile.kill()

    def update_from_map(self, layer_list):
        """Set up the tiles to destroy according to areas and switches."""
        # Said areas can be defined using Object Layers in Tiled and put
        # rectangles colliding with the tiles you want to destroy.
        # Provide a related_switch property to ensure which ones spawn
        self.objects.clear()
        for layer in layer_list:
            if isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    if "related_switch" in obj.properties and "destroyer" in obj.name:
                        args = map(round, (obj.x, obj.y, obj.width, obj.height))
                        if obj.properties["related_switch"] not in self.objects:
                            self.objects[obj.properties["related_switch"]] = [pygame.Rect(*args)]
                        else:
                            self.objects[obj.properties["related_switch"]].append(pygame.Rect(*args))


class SwitchSpawnManager:
    """Same as SwitchDestroyManager but handles the spawn"""

    def __init__(self, game):
        self.game = game
        self.objects = {}
        self.related_tiles = {}

    def spawn(self, switch: int):
        """Spawn the tiles associated with this switch."""
        if switch in self.related_tiles:
            for tile in self.related_tiles[switch]:
                self.game.tiles.add(tile, layer=0)
                self.game.objects.add(tile, layer=0)

    def update_from_map(self, layer_list):
        """Set up the tiles to spawn according to areas and switches."""
        # Said areas can be defined using Object Layers in Tiled and put
        # rectangles colliding with the tiles you want to destroy.
        # Provide a related_switch property to ensure which ones spawn
        self.objects.clear()
        self.related_tiles.clear()
        for layer in layer_list:
            if isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    if "related_switch" in obj.properties and "spawner" in obj.name:
                        args = map(round, (obj.x, obj.y, obj.width, obj.height))
                        if obj.properties["related_switch"] not in self.objects:
                            new_rect = pygame.Rect(*args)
                            self.objects[obj.properties["related_switch"]] = [new_rect]
                            tile_gen = [
                                tile
                                for tile in self.game.tiles.get_sprites_from_layer(0)
                                if tile.rect.colliderect(new_rect)
                            ]
                            for tile in tile_gen:
                                tile.kill()
                            self.related_tiles[obj.properties["related_switch"]] = pygame.sprite.Group(*tile_gen)
                        else:
                            new_rect = pygame.Rect(*args)
                            self.objects[obj.properties["related_switch"]].append(new_rect)
                            tile_gen = [
                                tile
                                for tile in self.game.tiles.get_sprites_from_layer(0)
                                if tile.rect.colliderect(new_rect)
                            ]
                            for tile in tile_gen:
                                tile.kill()
                            self.related_tiles[obj.properties["related_switch"]].add(*tile_gen)


class SwitchToggleManager:
    """Handles toggleable switch blocks."""

    def __init__(self, game):
        self.game = game
        self.objects = {}
        self.switch_blocks = {}

    def update_from_map(self, layer_list):
        """Update the toggleable tile list."""
        self.objects.clear()
        self.switch_blocks.clear()
        for layer in layer_list:
            if isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    print(obj)
                    props = obj.properties
                    if props is not None and obj.name is not None:
                        if "toggler" in obj.name and "related_switch" in props:
                            switch = props["related_switch"]
                            switch2 = props["related_other_switch"] if "related_other_switch" in props else None
                            args = map(round, (obj.x, obj.y, obj.width, obj.height))
                            new_rect = pygame.Rect(*args)
                            tile_gen = [
                                tile
                                for tile in self.game.tiles.get_sprites_from_layer(0)
                                if isinstance(tile, solid.SwitchBlock) and new_rect.colliderect(tile.rect)
                            ]
                            for tile in tile_gen:
                                if tile.tile_type - 1:
                                    tile.kill()
                            if switch in self.switch_blocks:
                                self.objects[switch].append(new_rect)
                                self.switch_blocks[switch].add(*tile_gen)
                            else:
                                self.objects[switch] = [new_rect]
                                self.switch_blocks[switch] = pygame.sprite.Group(*tile_gen)
                            if switch2 is not None:
                                if switch2 in self.switch_blocks:
                                    self.objects[switch2].append(new_rect)
                                    self.switch_blocks[switch2].add(*tile_gen)
                                else:
                                    self.objects[switch2] = [new_rect]
                                    self.switch_blocks[switch2] = pygame.sprite.Group(*tile_gen)

    def toggle(self, switch: int, status: bool):
        """Toggle the switch blocks."""
        if switch in self.objects:
            for s_block in self.switch_blocks[switch]:
                if s_block.tile_type - 1:
                    if status:
                        self.game.tiles.add(s_block, layer=0)
                        self.game.objects.add(s_block, layer=0)
                    else:
                        s_block.remove(self.game.tiles, self.game.objects)
                else:
                    if status:
                        s_block.remove(self.game.tiles, self.game.objects)
                    else:
                        self.game.tiles.add(s_block, layer=0)
                        self.game.objects.add(s_block, layer=0)


class EndingIncrementManager:
    """Override the default level increment for ending tiles."""

    def __init__(self, game):
        self.game = game
        self.objects = []

    def update_from_map(self, layer_list):
        """A nice doc string, duh."""
        self.objects.clear()
        for layer in layer_list:
            if isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    props = obj.properties
                    if "increase" in obj.name and "increment" in props:
                        new_rect = pygame.Rect(*map(round, (obj.x, obj.y, obj.width, obj.height)))
                        increment = props["increment"]
                        tile = list(tile for tile in self.game.tiles if tile.rect.colliderect(new_rect))[0]
                        print(tile)
                        self.objects.append((new_rect, increment))
                        tile.increment = increment


class TimedTileToggler:
    """Updates tiles in a delay."""

    def __init__(self, game):
        self.game = game
        self.time_delay = 0
        self.time_max = 0
        self.status = False
        self.objects = []
        self.tiles = []

    def update_from_map(self, layer_list):
        """Updates tiles from map."""
        self.time_delay = 0
        self.time_max = 0
        self.objects.clear()
        self.tiles.clear()
        self.status = False
        for layer in layer_list:
            if isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    if "timer_config" in obj.name:
                        self.time_max = obj.properties["max_delay"]
                    elif "timer" in obj.name:
                        new_rect = pygame.Rect(*map(round, (obj.x, obj.y, obj.width, obj.height)))
                        self.objects.append(new_rect)
                        tile_gen = [
                            tile
                            for tile in self.game.tiles.get_sprites_from_layer(0)
                            if isinstance(tile, solid.SwitchBlock) and tile.rect.colliderect(new_rect)
                        ]
                        self.tiles.extend(tile_gen)
                        for tile in tile_gen:
                            if tile.tile_type - 1:
                                tile.remove(self.game.tiles, self.game.objects)

    def update(self, dt):
        """Updates tiles."""
        if self.time_max:
            self.time_delay += dt
            if self.time_delay >= self.time_max:
                self.time_delay = 0
                self.status = not self.status
                for tile in self.tiles:
                    if tile.tile_type - 1:
                        if self.status:
                            self.game.tiles.add(tile, layer=0)
                            self.game.objects.add(tile, layer=0)
                        else:
                            tile.remove(self.game.tiles, self.game.objects)
                    else:
                        if self.status:
                            tile.remove(self.game.tiles, self.game.objects)
                        else:
                            self.game.tiles.add(tile, layer=0)
                            self.game.objects.add(tile, layer=0)


SPECIAL_LEVEL_MAPS = {"test": -1, "tutorial": 0}
LEVEL_SONGS = {
    0: "TheBuilder.mp3",
    1: "Sundays.mp3",
    2: "ShoppingList.mp3",
    3: "QuirkyDog.mp3",
    4: "Sundays.mp3",
    5: "ShoppingList.mp3",
    6: "TheBuilder.mp3",
    7: "QuirkyDog.mp3",
}


class Game:
    """The Game"""

    def __init__(self):
        self.player = player.Player(self)
        self.tiles = pygame.sprite.LayeredUpdates()
        self.other_players = pygame.sprite.Group()
        self.objects = pygame.sprite.LayeredUpdates(self.player)
        self.crashing = False
        self.showing_title = True
        self.inputting_nickname = False
        self.nickname = ""
        self.tmx_data: pytmx.TiledMap | None = None
        self.client = client.Client(self)
        self.level = 0
        self.camera = Camera(complex_camera, 160, 144)
        self.gui = pygame.sprite.Group(
            gui.Button((48, 90), "Play", self.start),
            gui.Button((110, 90), "Reset", self.del_cache),
            gui.Button((80, 110), "Exit Game", self.quit),
            gui.EmojiButton((148, 10), "♬", self.sound_on_off),
        )
        self.running = True
        self.showing_gui = True
        self.trigger_man = EventTriggerManager(self)
        self.switchd_man = SwitchDestroyManager(self)
        self.switchs_man = SwitchSpawnManager(self)
        self.switcht_man = SwitchToggleManager(self)
        self.ending_man = EndingIncrementManager(self)
        self.tile_timer = TimedTileToggler(self)
        self.sound = True
        mixer.play(-1)

    def quit(self):
        """Quit button event"""
        if self.client.running:
            self.client.stop()
        self.running = False
        pygame.quit()

    def sound_on_off(self):
        """ON/OFF for music."""
        if self.sound:
            mixer.pause()
            self.sound = False
        else:
            mixer.unpause()
            self.sound = True

    def load_next(self):
        """Load next map button event"""
        if os.path.isfile(f"maps/level{self.level+1}.tmx"):
            self.read_map(f"maps/level{self.level+1}.tmx")
        self.showing_gui = False
        self.gui.empty()

    def load_previous(self):
        """Load previous map button event"""
        if os.path.isfile(f"maps/level{self.level-1}.tmx"):
            self.read_map(f"maps/level{self.level-1}.tmx")
        self.showing_gui = False
        self.gui.empty()

    def go_back(self):
        """Closes the level menu."""
        self.showing_gui = False
        self.gui.empty()

    def start(self):
        """Start the game."""
        self.showing_gui = False
        self.showing_title = False
        nick = client.cache.get_nickname()
        if nick:
            self.gui.empty()
            self.client.start()
        else:
            self.show_input()

    def del_cache(self):
        """Delete local cache!"""
        client.cache.delete()

    def show_input(self):
        """Show the nickname text input."""
        self.showing_gui = True
        self.gui.empty()
        self.inputting_nickname = True
        self.gui.add(gui.TextInput(self))

    def crash(self):
        """<<Crash>> the game."""
        self.crashing = True
        mixer.pause()
        game_crash.play(-1)

    def read_map(self, directory):
        """This reads the TMX Map data"""
        # TMX is a variant of the XML format, used by the map editor Tiled.
        # Said maps use tilesets, stored in TSX files (which are also based on the XML format).
        self.tmx_data = pytmx.TiledMap(_resource_path(directory))
        if any(key for key in SPECIAL_LEVEL_MAPS if key in directory):
            self.level = SPECIAL_LEVEL_MAPS[list(key for key in SPECIAL_LEVEL_MAPS if key in directory)[0]]
        else:
            self.level = int(directory.removeprefix("maps/level").removesuffix(".tmx"))
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
                    if tile["tile"] == "spawnpoint":
                        self.player.rect.topleft = (tile_x * 16, tile_y * 16)
                        continue
                    if tile["tile"] == "npc":
                        self.tiles.add(solid.NPC(self, (tile_x, tile_y), layer), layer=layer)
                        continue
                    tile_id = tile["id"]
                    if tile_id not in [1, 20, 22, 25, 48, 49, 50]:
                        # Solid tile
                        new_spr = solid.Solid(self, (tile_x, tile_y), layer)
                        self._select_solid_image(new_spr, tile["type"], flipped_tile)
                        self.tiles.add(new_spr, layer=layer)
                    elif tile_id == 20:
                        # Level end tile.
                        self.tiles.add(solid.Ending((tile_x, tile_y)))
                    elif tile_id == 22:
                        # Shiny flag (tutorial tile)
                        self.tiles.add(solid.ShinyFlag((tile_x, tile_y)), layer=layer)
                    elif tile_id == 25:
                        # Switch (can be pressed by the player)
                        self.tiles.add(solid.Switch(self, (tile_x, tile_y)), layer=layer)
                    elif tile_id == 48:
                        self.tiles.add(solid.TempSwitch(self, (tile_x, tile_y)), layer=layer)
                    elif tile_id in [49, 50]:
                        self.tiles.add(solid.SwitchBlock(self, (tile_x, tile_y), layer, tile_id - 48), layer=layer)
                    else:
                        # "Glitchy" tile (starts a pseudo-crash upon contact)
                        self.tiles.add(solid.BuggyThingy(self, (tile_x, tile_y), layer), layer=layer)
        for sprite in self.tiles:
            self.objects.add(sprite, layer=self.tiles.get_layer_of_sprite(sprite))
        self.trigger_man.set_triggers(self.level)

        # Change song
        if self.sound:
            mixer.fadeout(3)
            mixer.unload()
            mixer.load(f"assets/{LEVEL_SONGS[self.level]}")
            mixer.play(-1)

        layers = self.tmx_data.layers
        self.switchd_man.update_from_map(layers)
        self.switchs_man.update_from_map(layers)
        self.switcht_man.update_from_map(layers)
        self.ending_man.update_from_map(layers)
        self.tile_timer.update_from_map(layers)

    def update_objects(self, *args, **kwargs):
        """Updates objects of the game."""
        layer1 = self.tiles.get_sprites_from_layer(1)
        layer1_collisions = pygame.sprite.spritecollide(
            self.player, layer1, False, lambda spr1, spr2: spr1.rect.clip(spr2.rect).size >= (2, 2)
        )
        if layer1_collisions:
            for sprite in layer1_collisions:
                if not isinstance(sprite, solid.NPC):
                    sprite.image.set_alpha(255 // 2)
            for sprite in layer1:
                if sprite in layer1_collisions:
                    continue
                sprite.image.set_alpha(255)
        else:
            for sprite in layer1:
                sprite.image.set_alpha(255)
        self.objects.update(*args, **kwargs)

    def draw_objects(self, screen):
        """
        Replacement for self.objects.draw.

        Designed to take the camera into account.
        """
        self.camera.update(self.player)
        for layer in self.objects.layers():
            sprites = self.objects.get_sprites_from_layer(layer)
            for sprite in sprites:
                if (not hasattr(sprite, "tile_type")) or sprite.tile_type != 40:
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
            case 21:
                img = solid.stone_block
            case 22:
                img = solid.cave_deep_gd
            case 23:
                img = solid.cave_bottom_gd
            case 24:
                img = solid.cave_bottom_corner_r if not flipped else solid.cave_bottom_corner_l
            case 25:
                img = solid.cave_bottom_corner_dual
            case 26:
                img = solid.cave_bottom_corner_single
            case 27:
                img = solid.cave_inward_bottom_corner_r if not flipped else solid.cave_inward_bottom_corner_l
            case 28:
                img = solid.cave_inward_bottom_corner_single
            case 29:
                img = solid.cave_inward_corner_r if not flipped else solid.cave_inward_corner_l
            case 30:
                img = solid.cave_inward_corner_single
            case 31:
                img = solid.cave_side_gd_l if not flipped else solid.cave_side_gd_r
            case 32:
                img = solid.cave_side_gd_r if not flipped else solid.cave_side_gd_l
            case 33:
                img = solid.cave_side_end_r if not flipped else solid.cave_side_end_l
            case 34:
                img = solid.cave_side_single
            case 35:
                img = solid.cave_side_gd_single
            case 36:
                img = solid.cave_single_gd
            case 37:
                img = solid.cave_normal_gd
            case 38:
                img = solid.cave_upper_corner_r if not flipped else solid.cave_upper_corner_l
            case 39:
                img = solid.cave_upper_corner_single
            case 40:
                img = solid.invisible_solid  # can be used for some tiles that don't blend well with the collision.
        tile.image = img.copy()
        tile.tile_type = type

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

    @staticmethod
    def render_ean_prompt(screen):
        """Render the "Enter a Nickname" message on screen."""
        text = gui.GUIItem.font.render("Enter a nickname", fgcolor=pygame.Color("black"))
        text[1].centerx = 80
        text[1].y = 16
        screen.blit(*text)

    @staticmethod
    def render_title(screen):
        """Render the title on screen."""
        screen.blit(title, (19, 32))

    @staticmethod
    def render_title_team(screen):
        """Render the title (with the team names)"""
        screen.blit(title_team, (19, 10))
