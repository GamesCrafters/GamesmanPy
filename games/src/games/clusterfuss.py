"""
Clusterfuss, by Mark Steere (July 2023).  https://marksteeregames.com

Two players, Red and Blue, on an N x N board initially filled with checkers in
a checkerboard pattern.  Red moves first.

MOVES        Every move is an orthogonal king capture: you move one of your own
             checkers one square up/down/left/right onto an occupied square,
             removing the checker that was there.  The captured checker may be
             friendly or enemy.  A move therefore always removes exactly one
             checker from the board (plus any enemy-only groups detached by it).

GROUPS       A group is a set of checkers (of either colour) connected
             orthogonally.  Diagonal adjacency is irrelevant.

RESTRICTION  A move is legal only if, afterwards, exactly one group contains
             checkers of the mover's colour.

REMOVAL      Any group detached by the move that contains only enemy checkers is
             immediately removed from the board, ending the turn.  Combined with
             the restriction above, exactly one group is left on the board at the
             end of every turn.

PASSING      Passing is not allowed, but a player with no legal move has their
             turn skipped.  The skip is modelled as a move, written '-'.

OBJECT       Remove all enemy checkers from the board.


STRING FORMATS
    Position (Readable)  side to move, then the board in row-major order from
                         the top-left square:  'x' Red, 'o' Blue, '-' empty.
                         e.g. 4x4 start -> 'xxoxooxoxxoxooxox'
    Move                 source square + direction, e.g. 'c4w'.  Squares are
                         named chess-style: file letter a.. left to right, rank
                         number 1.. bottom to top.  Directions are wasd
                         (w north, a west, s south, d east).  A skip is '-'.
"""

from models import Game, Value, StringMode
from typing import Optional

# --- cell contents ----------------------------------------------------------
EMPTY, RED, BLUE = 0, 1, 2

_CELL_TO_CHAR = {EMPTY: '-', RED: 'x', BLUE: 'o'}
_CHAR_TO_CELL = {'-': EMPTY, 'x': RED, 'o': BLUE}

# Pretty glyphs used by the TUI only.
_CELL_TO_GLYPH = {EMPTY: '.', RED: 'X', BLUE: 'O'}
_PLAYER_NAME = {RED: 'Red (X)', BLUE: 'Blue (O)'}

# --- move encoding ----------------------------------------------------------
# A move is  (source_index << 2) | direction,  where direction is one of:
UP, RIGHT, DOWN, LEFT = 0b00, 0b01, 0b10, 0b11
_DIR_TO_CHAR = {UP: 'w', LEFT: 'a', DOWN: 's', RIGHT: 'd'}

SKIP_STRING = '-'


class Clusterfuss(Game):
    id = 'clusterfuss'
    # Even by even only, so that both players start with the same number of
    # checkers.  6x6 is listed for completeness; it is almost certainly too
    # large to solve.
    variants = ["2x2", "4x4", "6x6"]
    n_players = 2
    # Every capture removes at least one checker, so no position can repeat.
    cyclic = False

    def __init__(self, variant_id: str):
        if variant_id not in Clusterfuss.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._rows = int(variant_id.split('x')[0])
        self._cols = int(variant_id.split('x')[1])
        self._n_cells = self._rows * self._cols
        # Sentinel move for a skipped turn.  Its source index is out of range of
        # any real square, so it can never collide with an encoded capture.
        self._skip_move = self._n_cells << 2

    # ------------------------------------------------------------------
    # Game interface
    # ------------------------------------------------------------------
    def start(self) -> int:
        """
        Returns the starting position of the game: a full checkerboard with Red
        on every square where (row + col) is even, and Red to move.
        """
        board = [
            RED if (r + c) % 2 == 0 else BLUE
            for r in range(self._rows)
            for c in range(self._cols)
        ]
        return self.hash(board, RED)

    def generate_moves(self, position: int) -> list[int]:
        (board, player) = self.unhash(position)
        if player not in board:
            return []
        moves = []
        for index in range(self._n_cells):
            if board[index] != player:
                continue
            for (dir, target) in self.neighbors(index):
                if board[target] == EMPTY:
                    continue
                after = board[:]
                after[target] = player
                after[index] = EMPTY
                # Legal only if exactly one group holds the mover's checkers.
                if sum(1 for group in self.groups(after)
                       if any(after[i] == player for i in group)) == 1:
                    moves.append((index << 2) | dir)
        return moves if moves else [self._skip_move]

    def do_move(self, position: int, move: int) -> int:
       
        (board, player) = self.unhash(position)
        if move != self._skip_move:
            (index, dir) = self.decode_move(move)
            target = self.step(index, dir)
            board[target] = player
            board[index] = EMPTY
            for group in self.groups(board):
                if not any(board[i] == player for i in group):
                    for i in group:
                        board[i] = EMPTY
        return self.hash(board, self.opponent(player))

    def primitive(self, position: int) -> Optional[Value]:
        
        (board, player) = self.unhash(position)
        if player not in board:
            return Value.Loss
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        (board, turn) = self.unhash(position)
        if mode == StringMode.TUI:
            return self.board_to_tui(board, turn)
        cells = ''.join(_CELL_TO_CHAR[cell] for cell in board)
        if mode == StringMode.AUTOGUI:
            return ('1_' if turn == RED else '2_') + cells
        return _CELL_TO_CHAR[turn] + cells

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable: the side to move followed by one
        character per cell, row-major from the top-left square.
        """
        if len(strposition) != self._n_cells + 1:
            raise ValueError("Position string has the wrong length")
        turn = _CHAR_TO_CELL[strposition[0]]
        if turn == EMPTY:
            raise ValueError("Position string has no side to move")
        board = [_CHAR_TO_CELL[c] for c in strposition[1:]]
        return self.hash(board, turn)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        if move == self._skip_move:
            return 'M_skip' if mode == StringMode.AUTOGUI else SKIP_STRING
        (index, dir) = self.decode_move(move)
        if mode == StringMode.AUTOGUI:
            return f'M_{index}_{self.step(index, dir)}_x'
        return self.square_name(index) + _DIR_TO_CHAR[dir]

    # ------------------------------------------------------------------
    # Rules helpers (core logic)
    # ------------------------------------------------------------------
    def is_legal(self, board: list[int], player: int) -> bool:
        """
        True if `board` (the position immediately after a capture, before any
        enemy-only group is removed) satisfies the move restriction: exactly one
        group contains checkers belonging to `player`.

        TODO(core).
        """
        pass

    def remove_enemy_only_groups(self, board: list[int], player: int) -> list[int]:
        """
        Returns a copy of `board` with every group that contains no checker of
        `player` cleared, as required by ENEMY-ONLY GROUP REMOVAL.

        TODO(core).
        """
        pass

    # ------------------------------------------------------------------
    # Board utilities
    # ------------------------------------------------------------------
    def groups(self, board: list[int]) -> list[list[int]]:
        """
        Returns the connected groups of `board` as lists of cell indices.
        Checkers of either colour connect; only orthogonal adjacency counts.
        """
        seen = [False] * self._n_cells
        groups = []
        for start in range(self._n_cells):
            if board[start] == EMPTY or seen[start]:
                continue
            seen[start] = True
            group = [start]
            frontier = [start]
            while frontier:
                index = frontier.pop()
                for (_, neighbor) in self.neighbors(index):
                    if board[neighbor] != EMPTY and not seen[neighbor]:
                        seen[neighbor] = True
                        group.append(neighbor)
                        frontier.append(neighbor)
            groups.append(group)
        return groups

    def neighbors(self, index: int) -> list[tuple[int, int]]:
        """
        Returns the (direction, index) pairs orthogonally adjacent to `index`.
        """
        (row, col) = self.get_coord(index)
        result = []
        if row > 0:
            result.append((UP, index - self._cols))
        if col < self._cols - 1:
            result.append((RIGHT, index + 1))
        if row < self._rows - 1:
            result.append((DOWN, index + self._cols))
        if col > 0:
            result.append((LEFT, index - 1))
        return result

    def step(self, index: int, dir: int) -> int:
        """
        Returns the index one square from `index` in `dir`.  Assumes the step
        stays on the board; callers get their directions from `neighbors`.
        """
        if dir == UP:
            return index - self._cols
        if dir == RIGHT:
            return index + 1
        if dir == DOWN:
            return index + self._cols
        return index - 1

    def opponent(self, player: int) -> int:
        return BLUE if player == RED else RED

    def square_name(self, index: int) -> str:
        """
        Returns the chess-style name of a cell index: file letter a.. from the
        left, rank number 1.. from the bottom.  Index 0 is the top-left square,
        so rank counts down from `self._rows`.
        """
        (row, col) = self.get_coord(index)
        return f'{chr(ord("a") + col)}{self._rows - row}'

    def board_to_tui(self, board: list[int], turn: int) -> str:
        """
        Returns the human-facing board drawing used by the TUI.
        """
        width = len(str(self._rows))
        pad = ' ' * width
        rule = f'{pad} +' + '-' * (2 * self._cols + 1) + '+'
        lines = [rule]
        for r in range(self._rows):
            cells = ' '.join(
                _CELL_TO_GLYPH[board[self.get_index(r, c)]] for c in range(self._cols)
            )
            lines.append(f'{self._rows - r:>{width}} | {cells} |')
        lines.append(rule)
        lines.append(f'{pad}   ' + ' '.join(chr(ord('a') + c) for c in range(self._cols)))
        lines.append(f'{pad} Turn: {_PLAYER_NAME[turn]}')
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------
    def hash(self, board: list[int], turn: int) -> int:
        """
        Packs the board (base 3, one trit per cell) and the side to move (lowest
        bit, 0 = Red) into a single integer.
        """
        position = 0
        for cell in reversed(board):
            position = position * 3 + cell
        return (position << 1) | (0 if turn == RED else 1)

    def unhash(self, position: int) -> tuple[list[int], int]:
        """
        Inverse of `hash`: returns (board, side to move).
        """
        turn = BLUE if position & 1 else RED
        position >>= 1
        board = []
        for _ in range(self._n_cells):
            board.append(position % 3)
            position //= 3
        return (board, turn)

    def decode_move(self, move: int) -> tuple[int, int]:
        """
        Inverse of the move encoding: returns (source index, direction).
        """
        return (move >> 2, move & 0b11)

    def get_coord(self, index: int) -> tuple[int, int]:
        return (index // self._cols, index % self._cols)

    def get_index(self, row: int, col: int) -> int:
        return row * self._cols + col
