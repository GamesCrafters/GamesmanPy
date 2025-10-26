from models import Game, Value
from typing import Optional

class Example(Game[int]):
    id = 'example'
    variants = ["a", "b", "c"]
    n_players = 2
    cyclic = False

    def start() -> int:
        """
        Returns the starting position of the puzzle.
        """
        pass
    
    def generate_moves(position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        pass
    
    def do_move(position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        pass

    def primitive(position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass

    