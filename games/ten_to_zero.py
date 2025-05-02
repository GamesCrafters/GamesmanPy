from models.game import Game, Value
from typing import Optional

class TenToZero(Game[int]):
    def __init__(self):
        self.id = 'ten-to-zero'
        self.n_players = 2
        self.cyclic = False

    def start(self) -> int:
        return 10
    
    def generate_moves(self, position: int) -> list[int]:
        return [x for x in [1, 2] if position - x >= 0]
    
    def do_move(self, position: int, move: int) -> int:
        return position - move
    
    def primitive(self, position) -> Optional[Value]:
        if position == 0:
            return Value.Loss
        else:
            return None