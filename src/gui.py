import pygame
import pygame.freetype  # needs to be imported explicitly
import pathlib
import os.path as path
from typing import Callable

pygame.freetype.init()  # must also be initialised explicitly and separately from the remainder of pygame


def _resource_path(file: str):
    """Return the absolute path for a file."""
    pathobj = pathlib.Path(file).absolute()
    return path.join(*pathobj.parts)


button = pygame.image.load(_resource_path("assets/button.png")).convert_alpha()
button_clicked = pygame.image.load(_resource_path("assets/button_clicked.png")).convert_alpha()


class Button(pygame.sprite.Sprite):
    _font = pygame.freetype.Font(_resource_path("assets/scj2022.ttf"), 9)
    _font.fgcolor = pygame.Color("white")

    def __init__(self, pos: tuple[int, int], text: str, func: Callable):
        super().__init__()
        self.pos = pos
        self.text = text
        self.func = func
        self._img_list = []
        self._init_img_list()
        self.image = self._img_list[0]
        self.rect = self.image.get_rect(topleft=pos)

    def update(self, *args, **kwargs):
        self.image = self._img_list[self.clicked]

    @property
    def clicked(self):
        return pygame.mouse.get_pressed()[0] and self.rect.collidepoint(pygame.mouse.get_pos())

    def click(self):
        self.func()

    def _init_img_list(self):
        # PRIVATE USE ONLY!
        text, text_rect = self._font.render(self.text)
        text_rect.width -= 5
        text_rect.height -= 1
        text = pygame.transform.scale(text, text_rect.size).convert_alpha()
        img = pygame.Surface((8 + text_rect.width, button.get_height())).convert_alpha()
        img2 = img.copy()
        for _ in range(2):
            img.blit(button, (0, 0), area=pygame.Rect(0, 0, 4, button.get_height()))
            img2.blit(button_clicked, (0, 0), area=pygame.Rect(0, 0, 4, button.get_height()))
            if not _:
                img = pygame.transform.flip(img, True, False)
                img2 = pygame.transform.flip(img2, True, False)
        text_rect.center = img.get_width() // 2, img.get_height() // 2
        button_slice = pygame.Rect(4, 0, 1, 16)
        for x in range(4, img.get_width() - 4):
            img.blit(button, (x, 0), area=button_slice)
            img2.blit(button_clicked, (x, 0), area=button_slice)
        img.blit(text, text_rect)
        img2.blit(text, text_rect)
        self._img_list.append(img)
        self._img_list.append(img2)
