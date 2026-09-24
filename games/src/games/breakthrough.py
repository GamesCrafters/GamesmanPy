from models import Game, Value, StringMode
from typing import Optional

class Breakthrough(Game):
    id = 'breakthrough'
    variants = ["3x5", "3x4"]
    n_players = 2
    cyclic = False

    # Most variants use 2 pawn rows per side; "3x4" is the small tutorial
    # board and uses just 1.
    _pawn_rows_by_variant = {"3x4": 1}

    # Directions are relative to the mover, not absolute board directions.
    _straight = 0b00
    _diag_left = 0b01
    _diag_right = 0b10

    # Named once so a typo here is a real error, not a silent string bug.
    _empty = '-'
    _o = 'o'
    _x = 'x'

    def __init__(self, variant_id: str):
        if variant_id not in Breakthrough.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        # variant_id looks like "3x5"
        self._cols = int(variant_id[0])
        self._rows = int(variant_id[2])
        self._pawn_rows = Breakthrough._pawn_rows_by_variant.get(variant_id, 2)

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        # Flat board: one char per cell.
        pos_arr = [Breakthrough._empty] * (self._rows * self._cols)
        # 'o' fills the first _pawn_rows rows (its home edge)...
        for row in range(self._pawn_rows):
            for col in range(self._cols):
                pos_arr[self.get_index(row, col)] = Breakthrough._o
        # ...'x' fills the last _pawn_rows rows (the opposite edge).
        for row in range(self._rows - self._pawn_rows, self._rows):
            for col in range(self._cols):
                pos_arr[self.get_index(row, col)] = Breakthrough._x
        # Trailing char records whose turn it is; 'o' moves first.
        pos_str = ''.join(pos_arr) + Breakthrough._o
        return self.hash(pos_str)

    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        pos_str = self.unhash(position)
        player = self.get_turn(pos_str)
        pos_str = pos_str[:-1]  # drop the turn char, we only need the board from here
        other_player = self._opponent(player)
        # 'o' moves toward increasing rows, 'x' toward decreasing rows.
        dr = 1 if player == Breakthrough._o else -1
        moves = []
        for (i, c) in enumerate(pos_str):
            if c != player:
                continue
            (row, col) = self.get_coord(i)
            target_row = row + dr
            if target_row < 0 or target_row >= self._rows:
                continue  # already on the far edge, no forward row exists
            # Pack (source index, row-direction bit, column direction) so
            # do_move/move_to_string can decode a move without the position
            # (move_to_string only ever receives the move).
            dr_bit = 1 if dr == 1 else 0
            move_base = (i << 3) | (dr_bit << 2)
            straight_i = self.get_index(target_row, col)
            if pos_str[straight_i] == Breakthrough._empty:
                # straight: only onto empty, never a capture
                moves.append(move_base | Breakthrough._straight)
            if col > 0:
                left_i = self.get_index(target_row, col - 1)
                if pos_str[left_i] in (Breakthrough._empty, other_player):
                    # diagonal: onto empty, or capturing an opponent pawn
                    moves.append(move_base | Breakthrough._diag_left)
            if col < self._cols - 1:
                right_i = self.get_index(target_row, col + 1)
                if pos_str[right_i] in (Breakthrough._empty, other_player):
                    moves.append(move_base | Breakthrough._diag_right)
        return moves

    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        pos_str = self.unhash(position)
        pos_arr = list(pos_str)
        (index, target_row, target_col) = self._decode_move(move)
        end_index = self.get_index(target_row, target_col)
        # Overwriting the target cell IS the capture; then clear the source.
        pos_arr[end_index] = pos_arr[index]
        pos_arr[index] = Breakthrough._empty
        prev_player = pos_arr[self._rows * self._cols]
        pos_arr[self._rows * self._cols] = self._opponent(prev_player)
        new_pos_str = ''.join(pos_arr)
        return self.hash(new_pos_str)

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal.
        """
        pos_str = self.unhash(position)
        player = self.get_turn(pos_str)  # the player about to move
        board = pos_str[:-1]
        other_player = self._opponent(player)
        # Normal-play convention: this describes the position from the mover's
        # perspective. If the opponent already reached the mover's home row, mover lost.
        home_row = 0 if player == Breakthrough._o else self._rows - 1
        for col in range(self._cols):
            if board[self.get_index(home_row, col)] == other_player:
                return Value.Loss
        # No legal moves (no pawns left, or fully blocked) is also a loss.
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
            autogui_player = '1_' if turn == Breakthrough._o else '2_'
            return autogui_player + pos_str[:-1]
        if mode == StringMode.TUI:
            # One row per line, highest row first, to visually match a real board.
            board = pos_str[:-1]
            rows = []
            for row in range(self._rows - 1, -1, -1):
                start = self.get_index(row, 0)
                rows.append(' '.join(board[start:start + self._cols]))
            return '\n'.join(rows)
        # Readable: the raw string exactly as hash()/from_string() expect, so it round-trips.
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
        direction = move & 0b11
        (start_index, target_row, target_col) = self._decode_move(move)
        if mode == StringMode.AUTOGUI:
            end_index = self.get_index(target_row, target_col)
            return f'M_{start_index}_{end_index}_x'
        dir_str = 'straight'
        if direction == Breakthrough._diag_left:
            dir_str = 'diag-left'
        elif direction == Breakthrough._diag_right:
            dir_str = 'diag-right'
        return f'{start_index}-{dir_str}'

    def get_turn(self, pos_str: str) -> str:
        # One extra trailing character: whose turn it is.
        return pos_str[-1]

    def _opponent(self, player: str) -> str:
        return Breakthrough._x if player == Breakthrough._o else Breakthrough._o

    def _decode_move(self, move: int) -> tuple[int, int, int]:
        """
        Returns (source_index, target_row, target_col) for a packed move.
        Shared by do_move and move_to_string so the encoding is only unpacked in one place.
        """
        direction = move & 0b11
        dr = 1 if (move >> 2) & 0b1 else -1
        source_index = move >> 3
        (row, col) = self.get_coord(source_index)
        target_col = col
        if direction == Breakthrough._diag_left:
            target_col = col - 1
        elif direction == Breakthrough._diag_right:
            target_col = col + 1
        return (source_index, row + dr, target_col)

    def hash(self, pos_str: str) -> int:
        # 2 bits per char: '-'=00, 'x'=01, 'o'=10. This int is what the solver/db store.
        position = 0
        for c in pos_str:
            position <<= 2
            piece = 0
            if c == Breakthrough._x:
                piece = 1
            elif c == Breakthrough._o:
                piece = 2
            position |= piece
        return position

    def unhash(self, position: int) -> str:
        # Inverse of hash(): peel 2 bits at a time from the low end, which are
        # the string's last characters, so fill pos_arr back-to-front.
        n_spaces = self._rows * self._cols
        pos_arr = [Breakthrough._empty] * (n_spaces + 1)
        for i in range(n_spaces, -1, -1):
            piece = position & 0b11
            if piece == 0b01:
                pos_arr[i] = Breakthrough._x
            elif piece == 0b10:
                pos_arr[i] = Breakthrough._o
            position >>= 2
        return ''.join(pos_arr)

    def get_coord(self, index: int) -> tuple[int, int]:
        # Inverse of get_index(): recover (row, col) from a flat index.
        row = index // self._cols
        col = index % self._cols
        return (row, col)

    def get_index(self, row: int, col: int) -> int:
        # Maps (row, col) onto its position in the flat board string.
        return row * self._cols + col
