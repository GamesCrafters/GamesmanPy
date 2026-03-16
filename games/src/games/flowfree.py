"""
Flow Free – 5×5 puzzle for GamesmanPuzzles
===========================================

SETUP INSTRUCTIONS
------------------
1. Copy this file to:  games/src/games/flowfree.py

2. In games/src/games/game_manager.py, add:
       from games.flowfree import FlowFree
   and append  FlowFree  to  game_list.

3. Solve from the project root:
       uv run solver flowfree          # all variants
       uv run solver flowfree -v a     # specific variant
       uv run solver flowfree -v a -o  # overwrite existing database

BOARD
-----
  5×5 grid, cells indexed 0-24  (cell = row * 5 + col)
  Colors  1-5  (0 = empty)

  Variant a (easy)      Variant b (medium)    Variant c (hard)
  R . B . R             R . B . G             R G . B .
  G . . M .             . Y . . .             Y . . . .
  Y . . . G             . M . M .             M . . . M
  . M . . .             . . . Y .             . . . . Y
  . . B . Y             R . B . G             . B . G R

STATE ENCODING  (single integer, fully reversible)
--------------------------------------------------
  hash(board, active_color, active_head)

  board        : 25 base-6 digits packed into an integer
                 board[i] in {0..5}, digit weight = 6^i
  active_color : which color is currently being drawn (0 = none)
                 stored in digit position 25  -> multiplied by 6^25
  active_head  : cell index of the path's current tip (NO_HEAD=25 if none)
                 stored in digit position 26  -> multiplied by 6^26

MOVES  (integer 0-24 = cell the player taps)
--------------------------------------------
  No active path -> tap any dot cell to start drawing that color
  Active path    -> tap an adjacent empty cell to extend the path
                    tap the partner dot to complete and lock the path
"""

from models import Game, Value, StringMode
from typing import Optional
# ── Constants ────────────────────────────────────────────────────────────────

SIZE    = 5
NCELLS  = SIZE * SIZE      # 25
BASE    = 6                # colors 1-5 plus 0 (empty)
NO_HEAD = NCELLS           # sentinel: 25 means "no path in progress"

COLOR_NAMES = {0: ".", 1: "R", 2: "G", 3: "B", 4: "Y", 5: "M"}

# ── Puzzle layouts ────────────────────────────────────────────────────────────
# {cell_index: color_id}  — only the fixed dot endpoints are listed.

PUZZLES = {
    "a": {                  # easy
         0: 1,  4: 1,       # Red
         5: 2, 14: 2,       # Green
         2: 3, 22: 3,       # Blue
        10: 4, 24: 4,       # Yellow
         8: 5, 16: 5,       # Maroon
    },
    "b": {                  # medium
         0: 1, 20: 1,       # Red
         4: 2, 24: 2,       # Green
         2: 3, 22: 3,       # Blue
         6: 4, 18: 4,       # Yellow
        11: 5, 13: 5,       # Maroon
    },
    "c": {                  # hard
         0: 1, 24: 1,       # Red   (opposite corners)
         1: 2, 23: 2,       # Green
         3: 3, 21: 3,       # Blue
         5: 4, 19: 4,       # Yellow
        10: 5, 14: 5,       # Maroon
    },
}


# ── Module-level helpers ──────────────────────────────────────────────────────

def _neighbors(cell: int) -> list[int]:
    """ since flow free is constricted with moves (horizontal or vertical no diagnol or overlap) need to nReturn valid neighbor cell indices for a given cell."""
    r, c = divmod(cell, SIZE)
    result = []
    if r > 0:        result.append((r - 1) * SIZE + c)
    if r < SIZE - 1: result.append((r + 1) * SIZE + c)
    if c > 0:        result.append(r * SIZE + c - 1)
    if c < SIZE - 1: result.append(r * SIZE + c + 1)
    return result


def _all_connected(board: list[int], dots: dict) -> bool:
    """Return True if every color's two dot endpoints are BFS-connected."""
    seen_colors = set()
    for cell, color in dots.items():
        if color in seen_colors:
            continue
        seen_colors.add(color)
        endpoints = [c for c, v in dots.items() if v == color]
        start, goal = endpoints[0], endpoints[1]
        visited, queue = {start}, [start]
        found = False
        while queue:
            cur = queue.pop()
            if cur == goal:
                found = True
                break
            for nb in _neighbors(cur):
                if nb not in visited and board[nb] == color:
                    visited.add(nb)
                    queue.append(nb)
        if not found:
            return False
    return True


# ── Game class ────────────────────────────────────────────────────────────────

class FlowFree(Game):
    id        = "theflow"
    variants  = ["a", "b", "c"]
    n_players = 1
    cyclic    = False

    def __init__(self, variant_id: str):
        if variant_id not in FlowFree.variants:
            raise ValueError(f"Unknown variant '{variant_id}'. Choose from {FlowFree.variants}.")
        self._variant_id    = variant_id
        self._dots          = PUZZLES[variant_id]        # {cell: color}
        self._dot_set       = set(self._dots.keys())     # fast membership test
        self._non_dot_cells = sorted(set(range(NCELLS)) - self._dot_set)  # 15 cells
        n                   = len(self._non_dot_cells)
        self._B_N           = BASE ** n        # multiplier for active_color slot
        self._B_N1          = self._B_N * BASE # multiplier for active_head slot

    # ── hash / unhash  (recommended helpers) ─────────────────────────────────

    def hash(self, board: list[int], active_color: int, active_head: int) -> int:
        """
        Pack (board, active_color, active_head) into a single integer.

        Only non-dot cells are encoded (dot cells are always their fixed color).
        non_dot_cells[j] occupies digit j in base-6  (weight = 6^j).
        active_color occupies the next digit  (weight = 6^15).
        active_head  occupies the next digit  (weight = 6^16).
        Max value ≈ 7.3e13, well within SQLite's 64-bit INTEGER range.
        """
        n = 0
        for i in range(len(self._non_dot_cells) - 1, -1, -1):
            n = n * BASE + board[self._non_dot_cells[i]]
        n += active_color * self._B_N
        n += active_head  * self._B_N1
        return n

    def unhash(self, position: int) -> tuple[list[int], int, int]:
        """
        Unpack an integer position back to (board, active_color, active_head).
        Inverse of hash().
        """
        active_head  = position // self._B_N1
        rest         = position  % self._B_N1
        active_color = rest // self._B_N
        rest         = rest  % self._B_N
        board = [0] * NCELLS
        for cell, color in self._dots.items():
            board[cell] = color
        for cell in self._non_dot_cells:
            board[cell] = rest % BASE
            rest //= BASE
        return board, active_color, active_head

    # ── start ─────────────────────────────────────────────────────────────────

    def start(self) -> int:
        """Return the starting position: dot endpoints placed, no active path."""
        board = [0] * NCELLS
        for cell, color in self._dots.items():
            board[cell] = color
        return self.hash(board, 0, NO_HEAD)

    # ── generate_moves ────────────────────────────────────────────────────────

    def generate_moves(self, position: int) -> list[int]:
        """
        Return a list of valid cell indices (0-24) the player may tap.

        No active path  ->  any dot cell starts a new path for that color.
        Active path     ->  adjacent empty cells extend the path;
                            the partner dot completes and locks it.
        """
        board, active_color, active_head = self.unhash(position)
        moves = []

        if active_color == 0:
            # Between paths: player picks any dot to begin drawing
            for cell in self._dot_set:
                moves.append(cell)
        else:
            # Mid-draw: only moves adjacent to the current head
            for nb in _neighbors(active_head):
                nb_val = board[nb]
                if nb_val == 0:
                    # Empty cell — valid extension
                    moves.append(nb)
                elif (nb in self._dot_set
                      and self._dots[nb] == active_color
                      and nb != active_head):
                    # Partner dot — valid completion
                    moves.append(nb)

        return moves

    # ── do_move ───────────────────────────────────────────────────────────────

    def do_move(self, position: int, move: int) -> int:
        """Apply a tap at cell `move` and return the resulting position."""
        board, active_color, active_head = self.unhash(position)

        if active_color == 0:
            # Start a new path at this dot
            new_color = self._dots[move]
            return self.hash(board, new_color, move)

        # Complete: tap the partner dot to lock the path
        if (move in self._dot_set
                and self._dots[move] == active_color
                and move != active_head):
            board[move] = active_color
            return self.hash(board, 0, NO_HEAD)

        # Extend: color the empty adjacent cell and advance the head
        board[move] = active_color
        return self.hash(board, active_color, move)

    # ── primitive ─────────────────────────────────────────────────────────────

    def primitive(self, position: int) -> Optional[Value]:
        """
        Only evaluated at rest states (active_color == 0, between moves).

        Win  — every cell filled AND every color pair connected.
        Loss — board not solved AND no moves remain (stuck).
        None — game still in progress.
        """
        board, active_color, _ = self.unhash(position)

        if active_color != 0:
            return None

        board_full = all(c != 0 for c in board)

        if board_full:
            # Board is full: either it's solved or it's a dead end
            if _all_connected(board, self._dots):
                return Value.Win
            return Value.Loss

        if not self.generate_moves(position):
            return Value.Loss

        return None

    # ── to_string ─────────────────────────────────────────────────────────────

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Autogui  ->  compact single-line:  '<25 digits>_<color>_<head>'
        Readable ->  pretty 5x5 grid with column/row labels.
                     The active path head is shown in lowercase.
        """
        board, active_color, active_head = self.unhash(position)

        if mode == StringMode.AUTOGUI:
            cells = "".join(str(c) for c in board)
            return f"{cells}_{active_color}_{active_head}"

        # Readable: labelled grid
        lines = ["  0 1 2 3 4"]
        for r in range(SIZE):
            row = f"{r} "
            for c in range(SIZE):
                idx = r * SIZE + c
                ch  = COLOR_NAMES[board[idx]]
                if active_color != 0 and idx == active_head:
                    ch = ch.lower()   # mark the active tip in lowercase
                row += ch + " "
            lines.append(row.rstrip())

        head_label   = str(active_head) if active_color != 0 else "-"
        active_label = COLOR_NAMES.get(active_color, "?")
        lines.append(f"Drawing: {active_label}   Head: {head_label}")
        return "\n".join(lines)

    # ── from_string ───────────────────────────────────────────────────────────

    def from_string(self, strposition: str) -> int:
        """
        Parse a position string (Autogui format) back to an integer.
        Expected format: '<25 digits>_<active_color>_<active_head>'
        """
        parts = strposition.strip().split("_")
        if len(parts) != 3:
            raise ValueError(
                f"Expected format '<cells>_<color>_<head>', got: {strposition!r}"
            )
        cells_str, ac_str, ah_str = parts
        if len(cells_str) != NCELLS:
            raise ValueError(f"Expected {NCELLS} cell digits, got {len(cells_str)}")
        board        = [int(ch) for ch in cells_str]
        active_color = int(ac_str)
        active_head  = int(ah_str)
        return self.hash(board, active_color, active_head)

    # ── move_to_string ────────────────────────────────────────────────────────

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Autogui  ->  raw integer string,  e.g. '13'
        Readable ->  'row,col' string,    e.g. '2,3'
        """
        if mode == StringMode.AUTOGUI:
            return str(move)
        r, c = divmod(move, SIZE)
        return f"{r},{c}"
