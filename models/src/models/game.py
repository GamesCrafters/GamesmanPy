from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
from collections.abc import Hashable
from enum import IntEnum

State = TypeVar('state', bound=Hashable)

class Value(IntEnum):
    Loss = 0
    Tie = 1
    Win = 2

class StringMode(IntEnum):
    Readable = 0
    AUTOGUI = 1


class Game(ABC, Generic[State]):
    def __init__(self):
        raise TypeError(f'{self.__class__.__name__} is a static class and should not be instantiated.')

    @staticmethod
    @abstractmethod
    def start() -> State:
        """
        Returns the starting position of the game.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def generate_moves(position: State) -> list[State]:
        """
        Returns a list of positions given the input position.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def do_move(position: State, move: State) -> State:
        """
        Returns the resulting position of applying move to position.
        """
        pass

    @staticmethod
    @abstractmethod
    def primitive(position: State) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass

    @staticmethod
    @abstractmethod
    def to_string(position: State, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        pass

    @staticmethod
    @abstractmethod
    def from_string(strposition: str) -> State:
        """
        Returns the position from a string representation of the position.
        """
        pass

    @staticmethod
    @abstractmethod
    def move_to_string(move: State, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        pass