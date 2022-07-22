import pygame

class Solid(pygame.sprite.Sprite):
    def __init__(self, tile_pos:tuple):
        super().__init__()
        self.tile_pos=tile_pos #tile_pos is a tuple of integers representing a tile's topleft corner coordinates
        #We'll only need to multiply these coords by 16 to have the real position

