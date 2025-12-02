from models import Game, Value, StringMode
from typing import Optional

class Horses(Game):
    id = 'horses'
    variants = ["regular"]
    n_players = 2
    cyclic = True

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Horses.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return 0
    
    def generate_moves(self, position: int) -> list[tuple[int]]:
        """
        Returns a list of positions given the input position.
        """
        (position_str, turn) = self.unhash(position)
        (x_count, o_count) = self.count(position_str)
        total_count = x_count + o_count
        moves = []
        center_char = position_str[8]
        if total_count == 6:
            for i in range(8):
                char = position_str[i]
                if char == turn:
                    next = (i + 1) % 8
                    prev = (i - 1) % 8
                    if position_str[next] == '-':
                        moves.append((i, next))
                    if position_str[prev] == '-':
                        moves.append((i, prev))
                    if center_char == '-':
                        moves.append((i, 8))
                if char == '-' and center_char == turn:
                    moves.append((8, i))
        else:
            for i in range(9):
                char = position_str[i]
                if char == '-':
                    moves.append((None, i))
        return moves

                
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        (position_str, turn) = self.unhash(position)
        next_turn = 'x' if turn == 'o' else 'o'
        position_arr = list(position_str)
        (source, dest) = move
        if source is None:
            position_arr[dest] = turn
        else:
            position_arr[dest] = position_arr[source]
            position_arr[source] = '-'
        return self.hash(''.join(position_arr), next_turn)


    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        (position_str, turn) = self.unhash(position)
        center = position_str[8]
        for i in range(4):
            start = position_str[i]
            end = position_str[(i + 4) % 8]
            if start == end and start == center and start != '-':
                return Value.Loss
        for i in range(8):
            first = position_str[i]
            second = position_str[(i + 1) % 8]
            third = position_str[(i + 2) % 8]
            if first == second and first == third and first != '-':
                return Value.Loss
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        (position_str, turn) = self.unhash(position)
        autogui_turn = '1' if turn == 'x' else '2'
        return autogui_turn + '_' + position_str

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        position_str = strposition[2:]
        turn = 'x' if strposition[0] == '1' else 'o'
        return self.hash(position_str, turn)

    def move_to_string(self, move: tuple[int], mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        (src, dest) = move
        if src is None:
            return f'A_-_{dest}_x'
        else:
            return f'M_{src}_{dest}_y'

    def hash(self, position_str: str, turn: str) -> int:
        pos = 0
        turn_int = 0b1 if turn == 'o' else 0
        for i in range(len(position_str)):
            pos <<= 2
            piece_char = position_str[i]
            piece = 0
            if piece_char == 'x':
                piece = 0b01
            elif piece_char == 'o':
                piece = 0b10
            pos |= piece
        pos <<= 1
        pos |= turn_int
        return pos
    
    def unhash(self, position: int) -> tuple[str, str]:
        position_arr = ['-'] * 9
        turn = position & 0b1
        position >>= 1
        turn_char = 'o' if turn == 0b1 else 'x'
        for i in range(8, -1, -1):
            piece = position & 0b11
            if piece != 0:
                piece_char = 'x' if piece == 0b01 else 'o'
                position_arr[i] = piece_char
            position >>= 2
        position_str = ''.join(position_arr)
        return (position_str, turn_char)
    
    def count(self, position_str: str) -> tuple[int]:
        x_count = position_str.count('x')
        o_count = position_str.count('o')
        return (x_count, o_count)

