from models.src.game import Game, Value
from typing import Optional

class Example(Game[int]):
    def __init__(self, variant_id: str = "default"):
        self.id = 'example'
        self.variant = variant_id
        self.n_players = 1
        self.cyclic = False

    def start(self) -> int:
        return 0
    
    def generate_moves(self, position: int) -> list[int]:
        age = 0b11



    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        mask_full = 0b111_111_111_111_111_111_111_111_111
        mask_piece = 0b111
        mask_token = 0b100
        mask_age = 0b11
        new_pos = position
        shift = 0
        # Decrement age
        for i in range(9):
            age = (position & mask_age) >> shift
            if age == 0b01:
                new_pos &= mask_full ^ mask_piece
            else:
                new_pos &= mask_full ^ mask_age
                new_age = age - 1
                new_pos |= new_age << shift
            mask_age >>= 3
            mask_piece >>= 3
            mask_token >>= 3
            shift += 3
        # Do move
        new_pos |= move
        return new_pos

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass

    def hash(position_str: str) -> int:
        h = 0
        for i in range(8, -1, -1):
            i *= 2
            token = position_str[i]
            age = int(position_str[i + 1])
            val = 0
            if token == 'o':
                val = 0b100
            val |= age
            h <<= 3
            h |= val
        return h
    
    def unhash(position: int) -> str:
        position_str = ''
        for i in range(9):
            val = position & 0b111
            token = ''
            if val == 0:
                token = '--'
            else:
                age = val & 0b11
                token = 'o' if val & 0b100 else 'x'
                token += str(age)
            position_str += token
            position >>= 3

            
    