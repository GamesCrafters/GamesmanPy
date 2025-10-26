from models import Game, Value
from typing import Optional

class TenToZero(Game[int]):
    id = 'ten-to-zero'
    variants = ['default']
    n_players = 2
    cyclic = False

    def start() -> int:
        return 10
    
    def generate_moves(position: int) -> list[int]:
        return [x for x in [1, 2] if position - x >= 0]
    
    def do_move(position: int, move: int) -> int:
        return position - move
    
    def primitive(position) -> Optional[Value]:
        if position == 0:
            return Value.Loss
        else:
            return None
    
    def from_string(stringpos: str) -> int:
        return int(stringpos)
    
    def move_to_string(move: int, mode) -> str:
        return str(move)

    def to_string(pos: int, mode) -> str:
        return str(pos)