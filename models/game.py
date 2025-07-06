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
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def start(self) -> State:
        """
        Returns the starting position of the puzzle.
        """
        pass
    
    @abstractmethod
    def generate_moves(self, position: State) -> list[State]:
        """
        Returns a list of positions given the input position.
        """
        pass
    
    @abstractmethod
    def do_move(self, position: State, move: State) -> State:
        """
        Returns the resulting position of applying move to position.
        """
        pass

    @abstractmethod
    def primitive(self, position: State) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass

    @abstractmethod
    def to_string(self, position: State, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        pass

    @abstractmethod
    def from_string(self, strposition: str) -> State:
        """
        Returns the position from a string representation of the position.
        """
        pass

    @abstractmethod
    def move_to_string(self, move: State) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        pass