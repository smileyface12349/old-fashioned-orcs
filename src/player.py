import pygame


class Player(pygame.sprite.Sprite):
    """This is our player class.

    We derive it from pygame.sprite.Sprite in order to benefit from the group system pygame has.
    """

    def __init__(self, game):
        super().__init__()  # we need this to ensure the sprite will work correctly with groups
        # This is the game object. We need it for collisions.
        self.game=game
        # Surfaces are image objects. We can replace this with assets once they're made
        self.image = pygame.Surface((16, 16)).convert_alpha()
        # convert_alpha is a method to allow us to use PNG images with transparency, and also make them faster to
        # render on-screen
        self.image.fill("blue")  # For now, our player is just a random blue square though.
        # We make a rectangle object, which can then be used to locate the sprite on the screen.
        self.rect = self.image.get_rect(center=(80, 72))
        # In Pygame, (0, 0) is the topleft corner of the screen.
        # Adding 1 to self.rect.x will move self.rect 1 pixel to the right.
        # And so adding 1 to self.rect.y will move self.rect 1 pixel downwards.
        self.x_velocity = 1
        self.y_velocity = 0
        self.falling=True
        self.fall_delay=0
        self.moving_right=False
        self.moving_left=False
    # The two methods below move the player.
    def move_left(self):
        """Moves the Player left"""
        self.rect.x -= self.x_velocity

    def move_right(self):
        """Moves the Player right"""
        self.rect.x+=self.x_velocity
    def update(self, dt):
        if self.moving_left:
            self.move_left()
        if self.moving_right:
            self.move_right()
        self.fall_sensor.midtop=self.rect.midbottom
        # Start falling only if there's no solid tile underneath the player and being on the same layer
        if (not self.falling) and \
                (not pygame.sprite.spritecollide(self, self.game.tiles, False,
                                                lambda spr1, spr2:spr1.fall_sensor.colliderect(spr2.rect) and \
                                                 not self.game.objects.get_layer_of_sprite(spr2))):
            self.falling=True
            self.y_velocity=1
        elif self.falling:
            pass

