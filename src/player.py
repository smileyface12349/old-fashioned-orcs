import pygame


class Player(pygame.sprite.Sprite):
    """This is our player class.

    We derive it from pygame.sprite.Sprite in order to benefit from the group system pygame has.
    """

    def __init__(self, game):
        super().__init__()  # we need this to ensure the sprite will work correctly with groups
        # This is the game object. We need it for collisions.
        self.game = game
        # Surfaces are image objects. We can replace this with assets once they're made
        self.image = pygame.Surface((16, 16)).convert_alpha()
        # convert_alpha is a method to allow us to use PNG images with transparency, and also make them faster to
        # render on-screen
        self.image.fill("blue")  # For now, our player is just a random blue square though.
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

    def jump(self):
        """Makes the Player jump."""
        if not self.jumping and not self.falling:
            self.jumping = True
            self.y_velocity = 6
            self.fall_delay = 0

    # The two methods below move the player.
    def move_left(self):
        """Moves the Player left"""
        self.rect.x -= self.x_velocity

    def move_right(self):
        """Moves the Player right"""
        self.rect.x += self.x_velocity

    def update(self, dt):
        """Auto-update the player"""
        tiles_on_same_layer = self.game.tiles.get_sprites_from_layer(0)
        if pygame.sprite.spritecollide(
            self,
            tiles_on_same_layer,
            False,
            lambda spr1, spr2: spr2.__class__.__name__ == "BuggyThingy" and spr1.rect.colliderect(spr2.rect),
        ):
            self.game.crash()
        if self.moving_left:
            left_collisions = pygame.sprite.spritecollide(
                self,
                tiles_on_same_layer,
                False,
                lambda spr1, spr2: spr2.playerisright_strict and spr1.rect.colliderect(spr2.rect),
            )
            if left_collisions:
                self.rect.x += 1
            self.x_velocity = int(not left_collisions)
            self.move_left()
        if self.moving_right:
            right_collisions = pygame.sprite.spritecollide(
                self,
                tiles_on_same_layer,
                False,
                lambda spr1, spr2: spr2.playerisleft_strict and spr1.rect.colliderect(spr2.rect),
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
                    tiles_on_same_layer,
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
                    tiles_on_same_layer,
                    False,
                    lambda spr1, spr2: spr2.playerisup_strict and spr1.rect.colliderect(spr2.rect),
                )

                if collisions:
                    self.rect.bottom = collisions[0].rect.y
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
                tiles_on_same_layer,
                False,
                lambda spr1, spr2: spr2.playerisdown_strict and spr1.rect.colliderect(spr2.rect),
            )
            if collisions:
                self.rect.y = collisions[0].rect.bottom
                self.y_velocity = 1
                self.fall_delay = 0
                self.jumping = False
                self.falling = True


class OtherPlayer(pygame.sprite.Sprite):
    """Another player, using another session."""

    def __init__(self, nickname, uuid):
        super().__init__()
        self.nickname = nickname
        self.uuid=uuid
        self.image=pygame.Surface((16, 16)).convert_alpha()
        self.image.fill("yellow")
        self.rect=self.image.get_rect()
