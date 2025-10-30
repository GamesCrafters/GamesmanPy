from abc import ABC, abstractmethod
from typing import Optional
from .util import Value, StringMode


class Game(ABC):
    @abstractmethod
    def __init__(self, variant_id: str):
        pass

    @abstractmethod
    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        raise NotImplementedError("start() not implemented.")
    
    @abstractmethod
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        raise NotImplementedError("generate_moves() not implemented.")
    
    @abstractmethod
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        raise NotImplementedError("do_move() not implemented.")

    @abstractmethod
    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        raise NotImplementedError("primitive() not implemented.")

    @abstractmethod
    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        raise NotImplementedError("to_string() not implemented.")

    @abstractmethod
    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        raise NotImplementedError("from_string() not implemented.")

    @abstractmethod
    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        raise NotImplementedError("move_to_string() not implemented.")