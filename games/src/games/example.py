from models import Game, Value, StringMode
from typing import Optional
from abc import abstractmethod

class Example(Game[int]):
    id = 'example'
    variants = ["a", "b", "c"]
    n_players = 2
    cyclic = False

    @abstractmethod
    def start() -> int:
        """
        Returns the starting position of the puzzle.
        """
        pass
    
    @abstractmethod
    def generate_moves(position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        pass
    
    @abstractmethod
    def do_move(position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        pass

    @abstractmethod
    def primitive(position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass

    @abstractmethod
    def to_string(position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        pass

    @abstractmethod
    def from_string(strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        pass

    @abstractmethod
    def move_to_string(move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        pass

    