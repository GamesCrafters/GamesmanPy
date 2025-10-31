from enum import IntEnum
from typing import Generic, TypeVar
from dataclasses import dataclass

T = TypeVar("T")
E = TypeVar("E")

class Value(IntEnum):
    Loss = 0
    Draw = 1
    Tie = 2
    Win = 3

class StringMode(IntEnum):
    Readable = 0
    AUTOGUI = 1
    TUI = 2

class Result(Generic[T, E]):
    def is_ok(self) -> bool:
        """
        Return true if this is an Ok() result, else false.
        """
        return isinstance(self, Ok)
    
    def is_err(self) -> bool:
        """
        Return true if this is an Err() result, else false.
        """
        return isinstance(self, Err)
    
    def unwrap(self) -> T:
        """
        Get the value wrapped in this result, if it is valid.
        """
        if self.is_ok():
            return self.value
        raise Exception("Called unwrap on err")
    
    def unwrap_err(self) -> E:
        """
        Get the error wrapped in this result, if it is an error.
        """
        if self.is_err():
            return self.error
        raise Exception("Called unwrap_err on non-error")
    def unwrap_or(self, default: T) -> T:
        """
        Get the value wrapped in the result, if it is valid, otherwise get the default value.
        """
        if self.is_ok():
            return self.value
        return default
    
@dataclass
class Ok(Result[T, E]):
    value: T

@dataclass
class Err(Result[T, E]):
    error: E
