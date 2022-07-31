import os.path as path
import pathlib

import pygame


def _resource_path(file: str):
    """Return the absolute path for a file."""
    pathobj = pathlib.Path(file).absolute()
    return path.join(*pathobj.parts)


player_right = pygame.image.load(_resource_path("assets/player.png")).convert_alpha()
# convert_alpha is a method to allow us to use PNG images with transparency, and also make them faster to
# render on-screen
player_left = pygame.transform.flip(player_right, True, False)
other_player_right = player_right.copy()
pygame.transform.threshold(
    other_player_right,
    player_right,
    pygame.Color("#4A4AFF"),
    set_color=pygame.Color("yellow"),
    inverse_set=True,
)  # if inverse_set were False, all pixels in player_right that were NOT set to a colour of #4A4AFF would be replaced
other_player_left = pygame.transform.flip(other_player_right, True, False)


class Player(pygame.sprite.Sprite):
    """This is our player class.

    We derive it from pygame.sprite.Sprite in order to benefit from the group system pygame has.
    """

    def __init__(self, game):
        super().__init__()  # we need this to ensure the sprite will work correctly with groups
        # This is the game object. We need it for collisions.
        self.game = game
        self.image = player_right
        self.direction = "r"
        # We make a rectangle object, which can then be used to locate the sprite on the screen.
        self.rect = self.image.get_rect(center=(80, 72))
        # self.fall_sensor is a Rect that we use to check if the player is standing on a tile.
        self.fall_sensor = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, 4)
        # In Pygame, (0, 0) is the topleft corner of the screen.
        # Adding 1 to self.rect.x will move self.rect 1 pixel to the right.
        # And so adding 1 to self.rect.y will move self.rect 1 pixel downwards.
        self.x_velocity = 1
        self.y_velocity = 0
        self.falling = True
        self.jumping = False
        self.jump_distance = 0
        self.fall_delay = 0
        self.moving_right = False
        self.moving_left = False
        self.mask = pygame.mask.from_surface(self.image)

    def jump(self):
        """Makes the Player jump."""
        if not self.jumping and not self.falling:
            self.jumping = True
            self.y_velocity = 6
            self.fall_delay = 0

    # The two methods below move the player.
    def move_left(self):
        """Moves the Player left"""
        if self.rect.x > 0:
            self.rect.x -= self.x_velocity
        self.direction = "l"

    def move_right(self):
        """Moves the Player right"""
        if self.rect.right < self.game.tmx_data.width * 16:
            self.rect.x += self.x_velocity
        self.direction = "r"

    def update(self, dt):
        """Auto-update the player"""
        if self.direction == "r":
            self.image = player_right
        else:
            self.image = player_left
        tiles_on_same_layer = self.game.tiles.get_sprites_from_layer(0)
        solids_on_same_layer = [
            tile
            for tile in tiles_on_same_layer
            if tile.__class__.__name__ in ("Solid", "NPC", "Switch", "TempSwitch", "SwitchBlock")
        ]
        if pygame.sprite.spritecollide(
            self,
            tiles_on_same_layer,
            False,
            lambda spr1, spr2: spr2.__class__.__name__ == "BuggyThingy" and pygame.sprite.collide_mask(spr1, spr2),
        ):
            self.game.crash()
        for tile in pygame.sprite.spritecollide(
            self,
            tiles_on_same_layer,
            False,
            lambda spr1, spr2: spr2.__class__.__name__ == "Ending" and pygame.sprite.collide_mask(spr1, spr2),
        ):
            # Go to next level
            try:
                i = tile.increment
            except AttributeError:
                i = 1
            if path.isfile(_resource_path(f"maps/level{self.game.level+i}.tmx")):
                self.game.read_map(f"maps/level{self.game.level+i}.tmx")
        if self.moving_left:
            left_collisions = pygame.sprite.spritecollide(
                self,
                solids_on_same_layer,
                False,
                lambda spr1, spr2: spr2.playerisright_strict
                and spr1.rect.colliderect(spr2.rect)
                and pygame.sprite.collide_mask(spr1, spr2),
            )
            if left_collisions:
                self.rect.x += 1
            self.x_velocity = int(not left_collisions)
            self.move_left()
        if self.moving_right:
            right_collisions = pygame.sprite.spritecollide(
                self,
                solids_on_same_layer,
                False,
                lambda spr1, spr2: spr2.playerisleft_strict
                and spr1.rect.colliderect(spr2.rect)
                and pygame.sprite.collide_mask(spr1, spr2),
            )
            if right_collisions:
                self.rect.x -= 1
            self.x_velocity = int(not right_collisions)
            self.move_right()

        # We update the fall sensor's position to stay underneath the player.
        self.fall_sensor.midtop = self.rect.midbottom
        if not self.jumping:
            # Start falling only if there's no solid tile underneath the player and being on the same layer
            if (not self.falling) and (
                not pygame.sprite.spritecollide(
                    self,
                    solids_on_same_layer,
                    False,
                    lambda spr1, spr2: spr1.fall_sensor.colliderect(spr2.rect),
                )
            ):
                self.falling = True
                self.y_velocity = 1
            elif self.falling:
                self.fall_delay += dt
                if self.fall_delay >= 18:
                    self.fall_delay = 0
                    self.rect.y += self.y_velocity
                    if self.y_velocity < 6:
                        self.y_velocity += 1
                collisions = pygame.sprite.spritecollide(
                    self,
                    solids_on_same_layer,
                    False,
                    lambda spr1, spr2: spr2.playerisup_strict
                    and spr1.rect.colliderect(spr2.rect)
                    and pygame.sprite.collide_mask(spr1, spr2),
                )

                if collisions:
                    self.rect.bottom = (
                        collisions[0].rect.y + 1 if collisions[0].rect.height == 16 else collisions[0].rect.centery - 2
                    )
                    for switch in filter(
                        lambda switch: "Switch" in switch.__class__.__name__
                        and "Block" not in switch.__class__.__name__,
                        collisions,
                    ):
                        switch.press()
                    self.y_velocity = 0
                    self.falling = False
                    self.fall_delay = 1
        else:
            self.fall_delay += dt
            if self.fall_delay >= 18:
                self.fall_delay = 0
                self.rect.y -= self.y_velocity
                if self.y_velocity:
                    self.y_velocity -= 1
                else:
                    self.jumping = False
                    self.falling = True
            collisions = pygame.sprite.spritecollide(
                self,
                solids_on_same_layer,
                False,
                lambda spr1, spr2: spr2.playerisdown_strict and spr1.rect.colliderect(spr2.rect),
            )
            if collisions:
                self.rect.y = collisions[0].rect.bottom
                self.y_velocity = 1
                self.fall_delay = 0
                self.jumping = False
                self.falling = True
            elif self.rect.y < 0:
                self.rect.y = 0
                self.y_velocity = 1
                self.fall_delay = 0
                self.jumping = False
                self.falling = True


class OtherPlayer(pygame.sprite.Sprite):
    """Another player, using another session."""

    def __init__(self, nickname, direction):
        super().__init__()
        self.nickname = nickname
        self.image = player_right
        self.direction = direction
        self.rect = self.image.get_rect()

    def update(self, *args, **kwargs):
        """Updates image of player depending on its facing direction"""
        if self.direction == "r":
            self.image = other_player_right
        else:
            self.image = other_player_left
