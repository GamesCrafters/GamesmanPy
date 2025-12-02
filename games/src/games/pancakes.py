from models import Game, Value, StringMode
from typing import Optional
import random
import math

class Pancakes(Game):
    id = 'pancakes'
    variants = ["5", "6", "7", "8"]
    n_players = 1
    cyclic = True

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Pancakes.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self.height = int(variant_id)
        self.factorials = [math.factorial(n) for n in range(0, self.height + 1)]

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        widths = [i + 1 for i in range(self.height)]
        direction_choices = [0, 1]
        random.shuffle(widths)
        directions = [random.choice(direction_choices) for _ in range(self.height)]
        return self.hash(widths, directions)
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        return list(range(0, self.height))
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        (widths, dirs) = self.unhash(position)
        widths[move:] = reversed(widths[move:])
        dirs[move:] = reversed(dirs[move:])
        dirs[move:] = [x ^ 0b1 for x in dirs[move:]]
        return self.hash(widths, dirs)

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        (widths, dirs) = self.unhash(position)
        correct_order = widths == sorted(widths, reverse=True)
        correct_direction = all(x == 0 for x in dirs)
        if correct_order and correct_direction:
            return Value.Win
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        pos_arr = []
        adder = ord('a') - 1
        (widths, dirs) = self.unhash(position)
        for i in range(self.height):
            val = str(widths[i]) if dirs[i] == 0 else chr(widths[i] + adder)
            pos_arr.append(val)
        pos_str = ''.join(pos_arr)
        return f'1_{pos_str}'


    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        widths = []
        dirs = []
        adder = ord('a') - 1
        strposition = strposition[2:]
        for char in strposition:
            if ord(char) > adder:
                dirs.append(1)
                widths.append(ord(char) - adder)
            else:
                dirs.append(0)
                widths.append(int(char))
        return self.hash(widths, dirs)



    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        return f'A_-_{move}_x'

    def hash(self, widths: list[int], directions: list[int]) -> int:
        h = 0
        n = self.height
        for i in range(n):
            count = self.count_lower(widths, i)
            h += count * self.factorials[n - i - 1]
        direction_hash = 0
        for dir in directions:
            direction_hash <<= 1
            direction_hash |= dir
        h = (h << n) | direction_hash
        return h

    def unhash(self, position: int) -> tuple[list[int]]:
        width_arr = []
        direction_arr = []
        n = self.height
        width_sorted = list(range(1, n + 1))
        for i in range(n):
            direction_arr.append(position & 0b1)
            position >>= 1
        for i in range(n - 1, -1, -1):
            f = self.factorials[i]
            val = width_sorted.pop(position // f)
            width_arr.append(val)
            position = position % f
        direction_arr.reverse()
        return (width_arr, direction_arr)

    def count_lower(self, widths: list[int], start_index: int) -> int:
        count = 0
        val = widths[start_index]
        for i in range(start_index + 1, len(widths)):
            if widths[i] < val:
                count += 1
        return count