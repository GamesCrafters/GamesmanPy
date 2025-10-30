from models import Game, Value, StringMode
from typing import Optional

class Clobber(Game):
    id = 'clobber'
    variants = ["3x4", "3x6", "5x3", "5x4"]
    n_players = 2
    cyclic = False
    _up = 0b00
    _right = 0b01
    _down = 0b10
    _left = 0b11
    def __init__(self, variant_id: str):
        if variant_id not in Clobber.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._cols = int(variant_id[0])
        self._rows = int(variant_id[2])


    def start(self) -> int:
        """
        Returns the starting position of the puzzle.
        """
        pos_str = ''.join(['o' if i % 2 == 0 else 'x' for i in range(self._rows * self._cols)]) + 'o'
        pos = self.hash(pos_str)
        return pos
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        pos_str = self.unhash(position)
        player = self.get_turn(pos_str)
        pos_str = pos_str[:-1]
        other_player = 'x' if player == 'o' else 'o'
        moves = []
        for (i, c) in enumerate(pos_str):
            (row, col) = self.get_coord(i)
            move_base = i << 2
            if c == player:
                if row > 0 and pos_str[i - self._cols] == other_player:
                    moves.append(move_base | Clobber._up)
                if row < self._rows - 1 and pos_str[i + self._cols] == other_player:
                    moves.append(move_base | Clobber._down)
                if col > 0 and pos_str[i - 1] == other_player:
                    moves.append(move_base | Clobber._left)
                if col < self._cols - 1 and pos_str[i + 1] == other_player:
                    moves.append(move_base | Clobber._right)
        return moves

        
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        pos_str = self.unhash(position)
        pos_arr = list(pos_str)
        dir = move & 0b11
        index = move >> 2
        end_index = 0
        match dir:
            case Clobber._up: end_index = index - self._cols
            case Clobber._right: end_index = index + 1
            case Clobber._down: end_index = index + self._cols
            case Clobber._left: end_index = index - 1
        pos_arr[end_index] = pos_arr[index]
        pos_arr[index] = '-'
        prev_player = pos_arr[self._rows * self._cols]
        pos_arr[self._rows * self._cols] = 'x' if prev_player == 'o' else 'o'
        new_pos_str = ''.join(pos_arr)
        return self.hash(new_pos_str)
        

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        if len(self.generate_moves(position)) == 0:
            return Value.Loss
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        pos_str = self.unhash(position)
        if mode == StringMode.AUTOGUI:
            turn = self.get_turn(pos_str)
            autogui_player = '1_' if turn == 'o' else '2_'
            pos_str = autogui_player + pos_str[:-1]
        return pos_str

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        return self.hash(strposition)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        dir = move & 0b11
        start_index = move >> 2
        if mode == StringMode.AUTOGUI:
            end_index = 0
            match dir:
                case Clobber._up: end_index = start_index - self._cols
                case Clobber._right: end_index = start_index + 1
                case Clobber._down: end_index = start_index + self._cols
                case Clobber._left: end_index = start_index - 1
            return f'M_{start_index}_{end_index}_x'
        dir_str = ''
        match dir:
            case Clobber._up: dir_str = 'up'
            case Clobber._right: dir_str = 'right'
            case Clobber._down: dir_str = 'down'
            case Clobber._left: dir_str = 'left'
        return f'{start_index}-{dir_str}'

    def get_turn(self, pos_str: str) -> str:
        return pos_str[-1]
        pieces = self._rows * self._cols
        odd = pieces % 2 == 1
        x_count = pos_str.count('x')
        o_count = pos_str.count('o')
        if odd:
            return 'o' if o_count == x_count + 1 else 'x'
        return 'o' if o_count == x_count else 'x'

    def hash(self, pos_str: str) -> int:
        position = 0
        for c in pos_str:
            position <<= 2
            piece = 0
            if c == 'x':
                piece = 1
            elif c == 'o':
                piece = 2
            position |= piece
        return position
    
    def unhash(self, position: int) -> str:
        n_spaces = self._rows * self._cols
        pos_arr = ['-'] * (n_spaces + 1)
        for i in range(n_spaces, -1, -1):
            piece = position & 0b11
            if piece == 0b01:
                pos_arr[i] = 'x'
            elif piece == 0b10:
                pos_arr[i] = 'o'
            position >>= 2
        return ''.join(pos_arr)
    
    def get_coord(self, index: int) -> tuple[int]:
        row = index // self._cols
        col = index % self._cols
        return (row, col)
    
    def get_index(self, row: int, col: int) -> int:
        return row * self._cols + col

    