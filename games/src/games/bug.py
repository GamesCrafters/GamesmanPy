from models import Game, Value, StringMode
from typing import Optional

"""Position: [player, 0 or 1] * 19 [what player is occupying]
Move: [move]n - 06, 0710, 0713, 0718, 08, 071114, 071114"""

class Bug(Game):
    id = 'bug'
    variants = ["regular"]
    n_players = 2
    cyclic = Falsefa

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
        # First, eat all the bugs
        # Second, return a list of available placement (1, ji)


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
        # you get a position like 101201201201201201200000 (20 digits, first digit is player turn indicator)
        # 130132 <- means change 34 to 1, which is white, change 12 to black
        #if no moves left, return 10 for white win, or 20 for black win
        return move

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        if position == 10 or position == 20:
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

    