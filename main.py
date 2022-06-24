import os
from game.game import Game
from itertools import permutations
import pygame

game1 = Game()
game1.get_all_possibles()
game1.game_loop()
