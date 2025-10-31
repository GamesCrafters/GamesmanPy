from models import Game, Value, StringMode
from typing import Optional

class Hanoi(Game):
    id = 'hanoi'
    variants = ["regular"]
    n_players = 1
    cyclic = False

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Hanoi.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        pass

    def start(self) -> int:
        """
        Returns the starting position of the puzzle.
        """
        pass
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        pass
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        pass

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        pass

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        pass

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        pass

    