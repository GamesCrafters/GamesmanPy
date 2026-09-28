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
    AUTOGUI              position '1_' (Red to move) or '2_' (Blue) + cells;
                         move 'M_<source index>_<target index>_x', skip 'M_skip'.


DATA REPRESENTATION
    Cell         EMPTY = 0, RED = 1, BLUE = 2.

    Board        A flat list of length rows * cols in row-major order, index 0
                 at the top-left.  Row numbers grow downward, so index 0 is
                 square a4 on 4x4 (not a1):

                     index            square name
                      0  1  2  3      a4 b4 c4 d4
                      4  5  6  7      a3 b3 c3 d3
                      8  9 10 11      a2 b2 c2 d2
                     12 13 14 15      a1 b1 c1 d1

                 get_coord(i) = (i // cols, i % cols);  get_index(r, c) =
                 r * cols + c;  square_name gives file 'a' + col, rank
                 rows - row.

    Direction    UP = 0, RIGHT = 1, DOWN = 2, LEFT = 3 (clockwise).  One step
                 changes the index by -cols, +1, +cols, -1 respectively.  The
                 string letters follow WASD instead: UP 'w', LEFT 'a', DOWN 's',
                 RIGHT 'd'.  `step` does no bounds checking, so directions
                 always come from `neighbors`, which drops off-board ones.

    Move         (source index << 2) | direction: the low two bits hold the
                 direction, the rest the source square.  On 2x2, a2d (index 0,
                 RIGHT) is 0b1 = 1 and b1a (index 3, LEFT) is 0b1111 = 15.  A
                 skip is n_cells << 2, whose source index is off the board, so it
                 cannot collide with a capture.

    Position     (board as a base-3 number << 1) | side to move, where cell i
                 has weight 3**i and the low bit is 0 for Red, 1 for Blue.  The
                 2x2 start [RED, BLUE, BLUE, RED] with Red to move is
                 (1 + 2*3 + 2*9 + 1*27) << 1 | 0 = 104.  The encoding space is
                 2 * 3**n_cells, but only a small fraction is reachable (about
                 520k positions on 4x4).
"""

from models import Game, Value, StringMode
from typing import Optional

# --- cell contents ----------------------------------------------------------
# One base-3 digit per cell in the position hash; RED and BLUE double as the
# side-to-move values.  See DATA REPRESENTATION above.
EMPTY, RED, BLUE = 0, 1, 2

_CELL_TO_CHAR = {EMPTY: '-', RED: 'x', BLUE: 'o'}
_CHAR_TO_CELL = {'-': EMPTY, 'x': RED, 'o': BLUE}

# Pretty glyphs used by the TUI only.
_CELL_TO_GLYPH = {EMPTY: '.', RED: 'X', BLUE: 'O'}
_PLAYER_NAME = {RED: 'Red (X)', BLUE: 'Blue (O)'}

# --- move encoding ----------------------------------------------------------
# A move is  (source_index << 2) | direction,  where direction is one of the
# values below, numbered clockwise.  Index delta per step: UP -cols, RIGHT +1,
# DOWN +cols, LEFT -1.
UP, RIGHT, DOWN, LEFT = 0b00, 0b01, 0b10, 0b11
# Move strings use WASD letters, which are not in clockwise order.
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
                if self.is_legal(after, player):
                    moves.append((index << 2) | dir)
        return moves if moves else [self._skip_move]

    def do_move(self, position: int, move: int) -> int:
        """
        Returns the position after `move`: the capture, then removal of any
        enemy-only groups, then the turn passes.  A skip only passes the turn.
        """
        (board, player) = self.unhash(position)
        if move != self._skip_move:
            (index, dir) = self.decode_move(move)
            board[self.step(index, dir)] = player
            board[index] = EMPTY
            board = self.remove_enemy_only_groups(board, player)
        return self.hash(board, self.opponent(player))

    def primitive(self, position: int) -> Optional[Value]:
        """
        The side to move loses once all of its checkers are gone.
        """
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
        """
        return sum(1 for group in self.groups(board)
                   if any(board[i] == player for i in group)) == 1

    def remove_enemy_only_groups(self, board: list[int], player: int) -> list[int]:
        """
        Returns a copy of `board` with every group that contains no checker of
        `player` cleared, as required by ENEMY-ONLY GROUP REMOVAL.
        """
        board = board[:]
        for group in self.groups(board):
            if not any(board[i] == player for i in group):
                for i in group:
                    board[i] = EMPTY
        return board

    # ------------------------------------------------------------------
    # Board utilities
    # ------------------------------------------------------------------
    def groups(self, board: list[int]) -> list[list[int]]:
        """
        Uses DFS.
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
        Packs the board and the side to move into a single integer, one-to-one.

        Idea: an integer can hold a row of digits, just as 352 holds 3, 5, 2
        (3*10**2 + 5*10**1 + 2*10**0).  Each cell has exactly three states
        (EMPTY 0, RED 1, BLUE 2), so we treat each cell as one base-3 digit,
        with cell i weighted 3**i:

            board value = board[0]*3**0 + board[1]*3**1 + ... + board[n-1]*3**(n-1)

        Base-3 representations are unique, so different boards give different
        values.  The side to move then goes in one extra base-2 digit at the
        very bottom, making the result a mixed-radix number:

            hash = board value * 2 + (0 if Red to move else 1)

        so an even hash means Red to move, an odd one Blue.  `<< 1` and `|` are
        just `* 2` and `+`.  Note the integer itself has no base; base 3 and
        base 2 are only the two ways the code reads its digits.

        Example, 2x2 start, board [RED, BLUE, BLUE, RED], Red to move:
            board value = 1*1 + 2*3 + 2*9 + 1*27 = 52   (base 3: 1221)
            hash        = 52 * 2 + 0            = 104
        """
        # Horner's rule: start from the most significant digit (the last cell)
        # and repeatedly shift everything up one base-3 place and add the next
        # cell, e.g. 0 -> 1 -> 5 -> 17 -> 52 for the example above.  Iterating
        # in reverse is what puts cell 0 in the lowest digit.
        position = 0
        for cell in reversed(board):
            position = position * 3 + cell
        # Make room for one bit (* 2) and store the side to move in it.
        return (position << 1) | (0 if turn == RED else 1)

    def unhash(self, position: int) -> tuple[list[int], int]:
        """
        Inverse of `hash`: returns (board, side to move).

        Peels digits off from the lowest end, in the reverse order `hash` put
        them in: first the base-2 turn digit, then one base-3 digit per cell.
        `% base` reads the lowest digit and `// base` drops it, just as
        352 % 10 = 2 and 352 // 10 = 35 in decimal.

        Example, 104:
            104 & 1 = 0 -> Red to move;  104 >> 1 = 52
            52 % 3 = 1, 52 // 3 = 17  -> board[0] = RED
            17 % 3 = 2, 17 // 3 = 5   -> board[1] = BLUE
             5 % 3 = 2,  5 // 3 = 1   -> board[2] = BLUE
             1 % 3 = 1,  1 // 3 = 0   -> board[3] = RED
        """
        # Lowest bit is the side to move (& 1 is % 2); >> 1 (// 2) drops it.
        turn = BLUE if position & 1 else RED
        position >>= 1
        # Cells come out in index order because cell 0 is the lowest digit.
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
