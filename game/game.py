import math
import os
import pygame
from models.piece import Piece
from models.player import Player
from copy import copy, deepcopy
import random as rnd
import ctypes

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
ANCHO, ALTO = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


# Metodo para dibujar texto en la pantalla
def draw_text(text: str, font, surface, x, y):
    textobj = font.render(text, 1, (0, 0, 0))
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)


class Game:
    player_playing: Player

    def __init__(self):  # Definicion de variables a usar
        self.updating = True  # señal para detener la actualizacion de la pantalla
        self.max_points = 50  # numero de puntos para ganar una partida
        self.max_depth = 2  # Profundidad maxima
        self.baraja = []  # Lista que almacena las piezas de la baraja
        self.crear_baraja()  # Funcion para crear las piezas de la baraja
        self.player_human = Player(False)  # Creacion de los jugadores
        self.player_machine = Player(True)
        self.who_start()  # Funcion para definir quien inicia
        self.distribute_pieces()  # Funcion para distribuir 14 piezas a cada jugador
        self.screen = pygame.display.set_mode((ANCHO - 100, ALTO - 100))  # Definicion de la pantalla y su tamaño
        pygame.display.set_caption("Rummyq")  # Titutlo de la pantalla
        self.running = True  # Señal para saber si el juego se continua ejecutando
        self.clock = pygame.time.Clock()  # Reloj auxiliar
        self.mouse_pos = []  # Lista para almacenar las coordenadas de la posicion del cursor
        self.jugada = []  # Lista para almacena una jugada escogida por un humano
        self.jugada_validated = []  # Lista para almacenar las jugadas validas
        self.validated = False  # Señal para saber si está validada
        self.jugada_machine = []  # Lista para almacenar las jugadas de la maquina
        pygame.font.init()

    # Valida si el cursor del mouse está en las coordenadas de la ficha
    def collide_validate(self, mouse, objeto):
        if (objeto[0] < mouse[0] < objeto[0] + objeto[2]) and (objeto[1] < mouse[1] < objeto[1] + objeto[3]):
            return True
        return False

    # Valida cada click en cada ficha
    def click_validate(self, pos_mouse, hand):
        for piece in hand:
            if self.collide_validate(pos_mouse, piece.get_coordinates() + (60, 110)):
                print(f"pulsado dentro de la ficha, {piece.value}, {piece.color}")
                self.jugada.append(piece)

    # Function que cambia el valor del comodin por el valor que se requiera en la jugada
    # jugada = [1, 2, 'COMODIN', 4], en este caso el comodin sería igual a 3
    def change_comodin(self, missing_value, jugada):
        for piece in jugada:
            if piece.color == 'COMODIN' and len(missing_value) != 0:
                piece.value = missing_value[0]
                print(f"valor nuevo del comodin: {piece.value}")

    # Funcion que recibe una Jugada y comprueba si es una jugada valida o no
    def validate_set(self, jugada):
        if len(jugada) < 3:  # Verifica que sea mayor a 3
            print("Tiene que seleccionar un minimo de 3 fichas")
            self.jugada.clear()
            return False
        missing_value = self.find_value_missing(jugada)  # Se obtiene la lista de valores faltantes
        self.change_comodin(missing_value, jugada)  # Se cambia el valor del comodin si lo hay
        for valor in range(1, len(jugada)):  # For para validar que la jugada esté ordenada de forma ascendente
            if jugada[valor].value < jugada[valor - 1].value:
                print("No está en orden")
                self.jugada.clear()
                return False
        consecutive = self.find_missing(jugada)  # Valida si la lista es de valores consecutivos
        equals = self.find_equals(jugada)  # Valida si la lista solo tiene valores iguales
        gt_30 = self.is_greather_than_30(jugada)
        if self.player_human.first_turn:
            self.player_human.first_turn = False
            if not gt_30:
                self.player_human.first_turn = False
                self.jugada.clear()
                print('La jugada del primer turno debe ser mayor a 30')
                return False
        if consecutive or equals:  # Si alguna de las dos es verdadera, se trata de una jugada valida
            print("Está ordenada y completa")
            self.jugada_validated.extend(self.jugada)  # Se agrega a la lista de jugadas validadas
            for piece in self.jugada:
                self.player_human.hand.remove(piece)  # Se remueven las piezas de la mano
            self.jugada.clear()  # se limpia la jugada
            return True
        else:
            print("Está ordenada pero incompleta o con numeros repetidos")
            self.jugada.clear()
            return False

    # Funcion que valida si el valor de una jugada es mayor a 30
    def is_greather_than_30(self, jugada):
        accum = 0
        for piece in jugada:
            accum += piece.value
        if accum >= 30:
            return True
        else:
            return False

    # Funcion que recibe una lista de piezas y valida si todos sus valores son iguales
    # Ejemplo: [2, 2, 2]
    def find_equals(self, lst):
        aux = lst[0].value
        decision = False
        for piece in lst[1:]:
            if piece.value == aux:
                decision = True
            else:
                decision = False
        return decision

    # Funcion que recibe una lista de piezas y valida que todos sus valores sean consecutivos
    # Ejemplo: [1, 2, 3]
    def find_missing(self, lst):
        if len(lst) != 0:
            aux = lst[0].value
            for piece in lst:
                if aux != piece.value:
                    return False
                aux += 1
            return True
        return True

    # Funcion que recibe una lista y retorna una nueva lista con los valores faltantes en la lista original
    # Ejemplo entrada [1, 3, 4, 6]; salida [2, 5]
    def find_value_missing(self, array):
        lst = []
        for piece in array:
            lst.append(piece.value)
        return [x for x in range(lst[0], lst[-1] + 1)
                if x not in lst]

    # Funcion que recibe las fichas de una mano y retorna la suma de sus valores
    def calculate_points(self, hand):
        accum = 0
        for piece in hand:
            accum += piece.value
        return accum

    # Funcion que caputa los eventos del juego y hace algo en consecuencia
    def events(self):
        for event in pygame.event.get():
            if self.player_machine.first_turn:  # Pregunta si la maquina tiene el primer turno
                self.try_possibles(max_depth=self.max_depth, alpha=-math.inf, beta=math.inf, maximin=True,
                                   initial=True)
                self.player_machine.first_turn = False
            if len(self.player_human.hand) == 0:  # Condicion para saber si algun jugador se quedo sin cartas en la mano
                points = self.calculate_points(self.player_machine.hand)
                self.player_human.points += points
                self.player_machine.points -= points
                print(f'Ganó el jugador: {self.player_human.nombre}')
                self.baraja.clear()
                self.player_human.hand.clear()
                self.player_machine.hand.clear()
                self.jugada_validated.clear()
                self.jugada_machine.clear()
                self.crear_baraja()
                self.distribute_pieces()
            if len(self.player_machine.hand) == 0:
                points = self.calculate_points(self.player_human.hand)
                self.player_machine.points += points
                self.player_human.points -= points
                print(f'Ganó el jugador: {self.player_machine.nombre}')
                self.baraja.clear()
                self.player_human.hand.clear()
                self.player_machine.hand.clear()
                self.jugada_validated.clear()
                self.jugada_machine.clear()
                self.crear_baraja()
                self.distribute_pieces()
            if event.type == pygame.QUIT:  # Para saber si se quiere cerrar la ventana
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:  # Para saber si se presionó un boton del mouse
                self.click_validate(pygame.mouse.get_pos(), self.player_human.hand)  # Llamado a validar el click
            if event.type == pygame.KEYDOWN:  # Para saber si se presiono una tecla
                if event.key == pygame.K_SPACE:  # Para saber si se presiono la tecla espacio
                    print("Se presionó espacio")
                    self.validated = self.validate_set(self.jugada)  # Se valida que sea una jugada valida
                    if self.validated:  # si lo es, se aplica la jugada, y se procede con el turno de la maquina
                        print("Turno de la machine")
                        self.try_possibles(max_depth=self.max_depth, alpha=-math.inf, beta=math.inf, maximin=True,
                                           initial=True)
                if event.key == pygame.K_r:  # Para saber si la tecla presionada fue la r para robar una ficha
                    print("Se presionó r para robar una ficha")
                    self.player_human.first_turn = False
                    self.jugada.clear()
                    if len(self.baraja) != 0:  # Si la baraja no esta vacia
                        random = rnd.randint(0, len(self.baraja) - 1)
                        self.player_human.hand.append(
                            self.baraja[random])  # se agrega una ficha aleatoria de la baraja a la mano
                        self.baraja.pop(random)  # y se remueva de la baraja
                        print("Turno de la machine")  # y se procede con el turno de la maquina
                        self.try_possibles(max_depth=self.max_depth, alpha=-math.inf, beta=math.inf, maximin=True,
                                           initial=True)
                    else:
                        # si la baraja está vacia, se reinicia el juego y se actualizan las puntuaciones
                        self.crear_baraja()
                        self.distribute_points(self.player_human.hand, self.player_machine.hand)
                        self.player_machine.hand.clear()
                        self.player_human.hand.clear()
                        self.clean_board()
                        self.distribute_pieces()

    # Funcion para limpiar las fichas del tablero
    def clean_board(self):
        self.jugada_validated.clear()
        self.jugada_machine.clear()

    # Funcion para distribuir los puntos
    # y determinar un ganador de la ronda en el caso de que la baraja se quede sin piezas
    def distribute_points(self, human_hand, machine_hand):
        accum1 = 0
        accum2 = 0
        for piece in human_hand:
            accum1 += piece.value
        for piece in machine_hand:
            accum2 += piece.value
        if accum1 < accum2:  # Si la suma de los valores de las cartas en la mano del jugador humano
            accum2 -= accum1  # es menor a las del jugador máquina, este será el ganador
            print('Gana el player humano')
            self.player_human.points += accum2
            self.player_machine.points -= accum2
        if accum2 < accum1:  # Si la suma de los valores de las cartas en la mano del jugador máquina
            accum1 -= accum2  # es menor a las del jugador humano, este será el ganador
            print('Gana el player maquina')
            self.player_machine.points += accum1
            self.player_human.points -= accum1

    # Funcion donde se dibujan todos los elementos de la pantalla
    def draw(self):
        self.screen.fill((155, 155, 155))
        pygame.draw.rect(self.screen, (0, 50, 0),
                         pygame.Rect(40, 100, ANCHO - 400, ALTO - 300))
        pygame.draw.line(self.screen, (155, 155, 155), (40, ALTO - 385), (ANCHO - 365, ALTO - 385), 10)
        game_tittle = pygame.font.SysFont('Comic Sans MS', 40)
        piece_tittle = pygame.font.SysFont('Comic Sans MS', 20)
        win_tittle = pygame.font.SysFont('Comic Sans MS', 20)
        draw_text('RummyQ', game_tittle, self.screen, ANCHO - 340, 40)
        draw_text(f'Player Machine: {self.player_machine.points}', piece_tittle, self.screen, ANCHO - 350, 120)
        draw_text(f'Player Human: {self.player_human.points}', piece_tittle, self.screen, ANCHO - 350, 600)
        if self.player_human.win:
            draw_text(f'¡Player Human Wins!', win_tittle, self.screen, ANCHO - 350, ALTO/2)
        if self.player_machine.win:
            draw_text(f'¡Player Machine Wins!', win_tittle, self.screen, ANCHO - 350, ALTO/2)
        self.draw_pieces()
        self.draw_set_human(self.jugada_validated)
        self.draw_set_machine(self.jugada_machine)

    @staticmethod
    def update():
        pygame.display.update()

    # Ciclo principla del juego
    def game_loop(self):
        while self.running:
            self.draw()
            if self.check_win(True):  # Siempre va a preguntar si hay un ganador
                self.updating = False
            self.events()
            self.update()
            self.clock.tick(60)

    # Funcion donde se crea la baraja
    def crear_baraja(self):
        images_yellow = list()
        for valor in range(1, 14):
            images_yellow.append(pygame.image.load(os.path.join("Fichas", f"{valor}Amarillo.png")))
        images_blue = list()
        for valor in range(1, 14):
            images_blue.append(pygame.image.load(os.path.join("Fichas", f"{valor}Azul.png")))
        images_red = list()
        for valor in range(1, 14):
            images_red.append(pygame.image.load(os.path.join("Fichas", f"{valor}Rojo.png")))
        images_black = list()
        for valor in range(1, 14):
            images_black.append(pygame.image.load(os.path.join("Fichas", f"{valor}Negro.png")))
        pieces = list()
        for valor in range(0, 13):
            pieces.append(Piece(valor + 1, "AMARILLO", images_yellow[valor]))
            self.baraja.append(Piece(valor + 1, "AMARILLO", images_yellow[valor]))
        for valor in range(0, 13):
            pieces.append(Piece(valor + 1, "AZUL", images_blue[valor]))
            self.baraja.append(Piece(valor + 1, "AZUL", images_blue[valor]))
        for valor in range(0, 13):
            pieces.append(Piece(valor + 1, "ROJO", images_red[valor]))
            self.baraja.append(Piece(valor + 1, "ROJO", images_red[valor]))
        for valor in range(0, 13):
            pieces.append(Piece(valor + 1, "NEGRO", images_black[valor]))
            self.baraja.append(Piece(valor + 1, "NEGRO", images_black[valor]))
        pieces.append(Piece(20, "COMODIN", pygame.image.load(os.path.join("Fichas", "Comodin.png"))))
        self.baraja.append(Piece(20, "COMODIN", pygame.image.load(os.path.join("Fichas", "Comodin.png"))))
        # self.baraja = copy(pieces)
        self.baraja.extend(pieces)
        rnd.shuffle(self.baraja)

    # Funcion donde se define quien empìeza a jugar segun las reglas del juego
    def who_start(self):
        num_piece = input("Digite la ficha que quiere elegir (0 a 105):  ")
        while not num_piece.isnumeric() or int(num_piece) > 105:  # Se asegura que solo se reciban numeros o numeros entre 0 y 105
            num_piece = input("Digite la ficha que quiere elegir (0 a 105) debe ser un numero:  ")
        print(f"La pieza seleccionada fue: {self.baraja[int(num_piece)].value} {self.baraja[int(num_piece)].color}")
        print(f"Ahora escoge {self.player_machine.nombre}")
        num_piece_machine = rnd.randint(0, 105)
        print(f"La pieza seleccionada fue: {self.baraja[num_piece_machine].value} "
              f"{self.baraja[num_piece_machine].color}")
        if self.baraja[int(num_piece)].value > self.baraja[num_piece_machine].value:
            self.player_human.first_turn = True
            print("Arranca el player humano")
        else:
            self.player_machine.first_turn = True
            print("Arranca el player maquina")

    # Funcion que distribuye 14 piezas a cada jugador y las remueve de la baraja
    def distribute_pieces(self):
        for valor in range(0, 14):
            self.player_human.hand.append(self.baraja[valor])
            self.baraja.pop(valor)
        for valor in range(0, 14):
            self.player_machine.hand.append(self.baraja[valor])
            self.baraja.pop(valor)
        print(f"Tamaño de la baraja {len(self.baraja)}")
        print(f"Tamaño de la mano humana {len(self.player_human.hand)}")
        print(f"Tamaño de la mano maquina {len(self.player_machine.hand)}")

    # Funcion que dibuja las piezas de la mano de cada jugador
    def draw_pieces(self):
        x, y = 40, 10
        for piece in self.player_machine.hand:
            picture = pygame.transform.scale(piece.image, [60, 110])
            self.screen.blit(picture, [x, y])
            piece.x = x
            piece.y = y
            x += 70
        x, y = 40, 550
        for piece in self.player_human.hand:
            picture = pygame.transform.scale(piece.image, [60, 110])
            self.screen.blit(picture, [x, y])
            piece.x = x
            piece.y = y
            x += 70
        pygame.display.flip()

    # Funcion que dibuja las piezas de la jugada del jugador humano
    def draw_set_human(self, jugada):
        x_set, y_set = 50, 370
        for piece in jugada:
            if x_set >= ANCHO - 400:  # AQUI EMPECE
                x_set = 50
                y_set += 110
            if y_set >= 480:
                self.jugada_validated.clear()
                break
            picture = pygame.transform.scale(piece.image, [60, 100])
            self.screen.blit(picture, [x_set, y_set])
            piece.x = x_set
            piece.y = y_set
            x_set += 80


    # Funcion que dibuja las piezas de la mano de un jugador maquina
    def draw_set_machine(self, jugada):
        x_set, y_set = 50, 170
        for piece in jugada:
            if x_set >= ANCHO - 400:
                x_set = 50
                y_set += 110
            if y_set >= 280:
                self.jugada_machine.clear()
                break
            picture = pygame.transform.scale(piece.image, [60, 100])
            self.screen.blit(picture, [x_set, y_set])
            piece.x = x_set
            piece.y = y_set
            x_set += 80


    # Funcion que retorna una lista de las posibles jugadas en la mano de la maquina
    def get_all_possibles(self):
        hand = self.player_machine.hand
        partial_set = []
        partial_equal = []
        partial_play = {}
        aux = []
        unique = set()
        # Piezas repetidas
        for piece in sorted(hand):  # Recorre la mano ordenada de menor a mayor
            partial_equal.append(piece.value)
            partial_set.append(piece.value)
            # print(piece.value)
        for valor in range(1, 14):  # For que crea la lista con las jugadas posibles con numerous repetidos
            if partial_equal.count(valor) == 3 or partial_equal.count(valor) == 4:
                for piece in hand:
                    if piece.value == valor:
                        partial_play[piece] = piece.value
                        if valor not in unique:
                            unique.add(valor)
                            aux.append([piece.value for i in range(partial_equal.count(valor))])
        # Piezas consecutivas
        consecutive = set(partial_set)
        lst_consecutive = list(consecutive)  # Lista sin fichas repetidas
        lst_aux = []

        # For que ajusta la lista de consecutivos para que no hayan numeros con diferencias mayores a 1 y -1 entre ellos
        # Ejemplo: lst_consecutive = [1, 2, 3, 5, 6, 7, 8] -> nueva lista = [1, 2, 3, 6, 7, 8]
        for i in range(len(lst_consecutive)):
            try:
                if lst_consecutive[-1] - 1 == lst_consecutive[i - 1] \
                        or lst_consecutive[i] + 1 == lst_consecutive[i + 1] \
                        or (lst_consecutive[i] - 1 == lst_consecutive[i - 1]):
                    lst_aux.append(lst_consecutive[i])
            except:
                print("Lista desbordada")
        solution = []
        lista = lst_aux
        # For para crear una lista con la lista de posibles combinaciones de 3 o mas numeros
        # Ejemplo: lst = [8, 9, 10, 11] -> new lst = [[8, 9, 10, 11], [9, 10, 11]]
        for i, x in enumerate(lista):
            temp = [x]
            if i >= len(lista) - 2:
                break
            for j in range(i + 1, len(lista)):
                if lista[j] == x + 1:
                    temp.append(lista[j])
                    x = lista[j]
                else:
                    break
            if len(temp) >= 3:
                solution.append(temp)
        solution.sort(key=len)  # Ordena la lista de listas por tamaño

        print(f'consecutivos: {lst_aux}')
        print(solution)
        print(aux)
        plays = []  # Lista donde se guardan todas las posibles jugadas
        plays.extend(aux)
        plays.extend(solution)
        print(f'Totales: {plays}')
        return plays

    # Funcion donde se implementan las podas alfa beta
    def try_possibles(self, max_depth, alpha, beta, maximin, initial):
        plays = self.get_all_possibles()  # Se obtienen las posibles jugadas
        best_play = []
        if len(plays) == 0:  # Si no hay jugadas, entonces la maquina roba una carta
            self.robar()
        else:
            for lst in plays:  # Se itera sobre estas jugadas
                value_play = sum(lst)
                score = self.minimax(max_depth - 1, alpha, beta, not maximin)  # Se obtiene el valor del minimax
                best_score = -math.inf if maximin else math.inf
                if maximin:  # Si está maximizando se comparan los score y se actualizan los valores
                    if score > best_score:
                        best_play = lst
                        alpha = max(alpha, score)
                        if beta <= alpha:  # si beta es menor a alpha, se rompe el cicle
                            break
                else:  # lo mismo pero en el caso de que no se maximice
                    if score < best_score:
                        best_score = score
                        best_play = lst
                        beta = min(beta, score)
                        if beta <= alpha:
                            break
            if initial:  # Si la funcion es llamada por el evento de presionar la tecla espacio, se aplica el mejor movimiento
                self.apply_best_move(best_play)
                print(f'best_play: {best_play}')
            else:
                return best_score

    # Funcion para saber si todos los numeros de una lista son iguales
    def all_equals(self, lst):
        valor = lst[0]
        deci = False
        for i in lst[1:]:
            if valor == i:
                deci = True
            else:
                deci = False
        return deci

    # Funcion que añade las piezas correspondientes a la lista de jugadas de la maquina
    def apply_best_move(self, play):
        if self.player_machine.first_turn and sum(play) < 30:
            print('La primer jugada debe sumar 30')
            self.player_machine.first_turn = False
            self.robar()
        elif self.all_equals(play):
            self.player_machine.first_turn = False
            for valor in play:
                for piece in self.player_machine.hand:
                    if piece.value == valor:
                        self.jugada_machine.append(piece)
                        self.player_machine.hand.remove(piece)
        else:
            self.player_machine.first_turn = False
            for valor in play:
                for piece in self.player_machine.hand:
                    if piece.value == valor:
                        self.jugada_machine.append(piece)
                        self.player_machine.hand.remove(piece)
                        break

    # Implementacion de minimax
    def minimax(self, depth, alpha, beta, maximin):
        if depth == 0 or self.check_win():  # Si la profuniddad es 0 o hay un ganador se retorna
            return self.evaluate()  # el valor de la heuristica

        if maximin:
            return self.try_possibles(max_depth=depth, alpha=alpha, beta=beta, maximin=True, initial=False)
        else:
            return self.try_possibles(max_depth=depth, alpha=alpha, beta=beta, maximin=False, initial=False)

    # Heuristica, compara el tamaño de las manos
    # Si la mano de la maquina es menor, lo toma como si estuviera ganando
    def evaluate(self):
        accum1 = 0
        accum2 = 0
        pieces_in_hand_human = len(self.player_human.hand)
        pieces_in_hand_machine = len(self.player_machine.hand)
        if pieces_in_hand_machine <= pieces_in_hand_human:
            accum1 += 1000
            accum2 -= 1000
        else:
            accum2 += 1000
            accum1 -= 1000

        return accum1 - accum2

    # Funcion que retorna si hay un ganador, comparando el puntjae de cada jugador con el puntaje maximo definido
    def check_win(self, change_value=False):
        win_human = self.player_human.points >= self.max_points
        win_machine = self.player_machine.points >= self.max_points
        if change_value:
            self.player_human.win = win_human
            self.player_machine.win = win_machine

        return win_human or win_machine

    # Funcion para que la maquina robe una carta
    def robar(self):
        if len(self.baraja) != 0:
            random = rnd.randint(0, len(self.baraja) - 1)
            self.player_machine.hand.append(self.baraja[random])
            self.baraja.pop(random)
            print("La maquina roba una carta")
        else:
            print("No hay mas cartas en la baraja, se reinicia el juego")
            self.crear_baraja()
            self.distribute_points(self.player_human.hand, self.player_machine.hand)
            self.player_machine.hand.clear()
            self.player_human.hand.clear()
            self.clean_board()
            self.distribute_pieces()
        return 1
