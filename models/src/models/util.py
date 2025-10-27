from enum import IntEnum
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")

class Value(IntEnum):
    Loss = 0
    Tie = 1
    Win = 2

class StringMode(IntEnum):
    Readable = 0
    AUTOGUI = 1

class Result(Generic[T, E]):
    def __init__(self, value: T = None, error: E = None):
        self._value = value
        self._error = error
    
    @staticmethod
    def ok(value: T):
        return Result(value=value)
    
    @staticmethod
    def err(error: E):
        return Result(error=error)
    
    def is_ok(self) -> bool:
        return self._error is None
    
    def is_err(self) -> bool:
        return self._error is not None
    
    def unwrap(self) -> T:
        if self.is_ok():
            return self._value
        raise Exception("Called unwrap on err")
    
    def unwrap_err(self) -> E:
        if self.is_err():
            return self._error
        raise Exception("Called unwrap_err on non-error")