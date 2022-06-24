import os.path
from copy import copy
import pygame


class Piece:

    def __init__(self, value, color, image):
        self.value = value
        self.color = color
        self.image = image
        self.reverse_image = pygame.image.load(os.path.join("Fichas", "Reverso.png"))
        self.x = 0
        self.y = 0

    def get_coordinates(self):
        return self.x, self.y

    def __gt__(self, piece):
        return self.value > piece.value
