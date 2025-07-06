from models.game import Game, Value
from typing import Optional

class Example(Game[int]):
    def __init__(self, variant_id: str = "default"):
        self.id = 'example'
        self.variant = variant_id
        self.n_players = 1
        self.cyclic = False

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

    