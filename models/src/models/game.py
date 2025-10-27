from abc import ABC, abstractmethod
from typing import Optional
from .util import Value, StringMode


class Game(ABC):
    def __init__(self):
        raise TypeError(f'{self.__class__.__name__} is a static class and should not be instantiated.')

    @staticmethod
    @abstractmethod
    def start() -> int:
        """
        Returns the starting position of the game.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def generate_moves(position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def do_move(position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        pass

    @staticmethod
    @abstractmethod
    def primitive(position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass

    @staticmethod
    @abstractmethod
    def to_string(position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        pass

    @staticmethod
    @abstractmethod
    def from_string(strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        pass

    @staticmethod
    @abstractmethod
    def move_to_string(move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        pass