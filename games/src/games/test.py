from models import Game, Value, StringMode
from typing import Optional

class Test(Game):
    id = 'test'
    variants = ["regular"]
    n_players = 1
    cyclic = False

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Test.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        pass

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return 1
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        if position == 1:
            return [2, 3]
        elif position == 2:
            return [4, 5]
        elif position == 4:
            return [2]
        return []
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        return move

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        if position == 3:
            return Value.Win
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        return str(position)

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        return int(strposition)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        return str(move)

    