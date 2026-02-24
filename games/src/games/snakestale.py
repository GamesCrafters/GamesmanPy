from GamesmanPy import models 
from models import Game, Value, StringMode

class Snakestale(Game):
    id = "snakestale"
    variants = ["4x4"]
    n_players = 1
    cyclic = True

    def __init__(self, variant_id: str, goal: tuple):
        if variant_id not in Snakestale.variants:
            raise ValueError("variant not defined")
        self.variant_id = variant_id
        self.goal = goal
        self.snake_len = 4
        self.hole_pos = 0
        self.cols = 4
        self.rows = 4

    
    def start(self):
        pos_str = [7, 3, 2, 1]
        pos = self.hash(pos_str)
        return pos


    def generate_moves(self, position: int):
        snake = self.unhash(position)
        head = snake[0]
        r, c = divmod(head, self.cols)

        moves =[]
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                target = nr * self.cols + nc
                if target not in snake:
                    moves.append(target)
        return moves 


    def do_move(self, position: int, move):
        snake = self.unhash(position)
        new_snake = [move] + snake[:-1]
        return self.hash(new_snake)

    def primitive(self, position: int): 
        snake = self.unhash(position)

        if snake[0] == self.hole_pos:
            return Value.Win
        
        if not self.generate_moves(position):
            return Value.Loss

    def hash(self, snake_list: list[int]) -> int:
        position = 0
        for pos in snake_list:
            position = (position << 4) | pos
        return position
    
    def unhash(self, position: int) -> list[int]:
        snake = []
        temp_pos = position
        for i in range(self.snake_len):
            snake.append(temp_pos & 0xF)
            temp_pos >>= 4
        return snake[::-1]