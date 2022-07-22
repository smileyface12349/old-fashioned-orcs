from .solid import *

class Player(pygame.sprite.Sprite):
    #This is our player class. We derive it from pygame.sprite.Sprite in order to benefit from the group system pygame has.
    def __init__(self):
        super().__init__() #we need this to ensure the sprite will work correctly with groups
        self.image=pygame.Surface((16, 16)).convert_alpha() #Surfaces are image objects. We can replace this with assets once they're made
        #convert_alpha is a method to allow us to use PNG images with transparency, and also make them faster to render on-screen
        self.image.fill("blue") #For now, our player is just a random blue square though.
        self.rect=self.image.get_rect() #We make a rectangle object, which can then be used to locate the sprite on the screen.
        #In Pygame, (0, 0) is the topleft corner of the screen. Adding 1 to self.rect.x will move self.rect 1 pixel to the right
        #And so adding 1 to self.rect.y will move self.rect 1 pixel downwards.
        self.x_velocity=1
        self.y_velocity=1

