class Player:
    def __init__(self, is_machine):
        self.is_machine = is_machine
        self.points = 0
        self.win = False
        self.enemy_player = None
        self.first_turn = False
        self.hand = []
        self.turn = 1
        if is_machine:
            self.nombre = "Machine_Player"
        else:
            self.nombre = "Human_Player"
