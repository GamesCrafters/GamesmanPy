from models import Game, Value, StringMode
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────

SIZE    = 5
NCELLS  = SIZE * SIZE  # 25
BASE    = 6            # colors 1-5 plus 0 (empty)
NO_HEAD = NCELLS       # sentinel: 25 = no path in progress

COLOR_NAMES = {0: ".", 1: "R", 2: "G", 3: "B", 4: "Y", 5: "M"}

# ── Puzzle layouts ────────────────────────────────────────────────────────────
# {cell_index: color_id}  — only the fixed dot endpoints are listed.

# Each puzzle is verified to have a valid board-filling solution.
#
# Variant a:       Variant b:       Variant c:
#   R G . . B        R G . . B        R . . . .
#   . . Y . .        . Y . . M        G Y M . .
#   M R . . .        . . G . .        . . B . .
#   . Y . . .        . . Y . .        . Y . M .
#   . . M G B        . . R B M        . G . B R
#
PUZZLES = {
    "a": {
         0: 1, 11: 1,       # Red
         1: 2, 23: 2,       # Green
         4: 3, 24: 3,       # Blue
         7: 4, 16: 4,       # Yellow
        10: 5, 22: 5,       # Maroon
    },
    "b": {
         0: 1, 22: 1,       # Red
         1: 2, 12: 2,       # Green
         4: 3, 23: 3,       # Blue
         6: 4, 17: 4,       # Yellow
         9: 5, 24: 5,       # Maroon
    },
    "c": {
         0: 1, 24: 1,       # Red
         5: 2, 21: 2,       # Green
        12: 3, 23: 3,       # Blue
         6: 4, 16: 4,       # Yellow
         7: 5, 18: 5,       # Maroon
    },
}

# Precomputed neighbor lists
_NEIGHBORS: list[list[int]] = []
for _cell in range(NCELLS):
    _r, _c = divmod(_cell, SIZE)
    _nb = []
    if _r > 0:        _nb.append((_r - 1) * SIZE + _c)
    if _r < SIZE - 1: _nb.append((_r + 1) * SIZE + _c)
    if _c > 0:        _nb.append(_r * SIZE + _c - 1)
    if _c < SIZE - 1: _nb.append(_r * SIZE + _c + 1)
    _NEIGHBORS.append(_nb)


# ── Module-level helpers ──────────────────────────────────────────────────────

def _color_connected(board: list[int], start: int, goal: int, color: int) -> bool:
    """Return True if start and goal are BFS-connected through same-colored cells."""
    visited, queue = {start}, [start]
    while queue:
        cur = queue.pop()
        if cur == goal:
            return True
        for nb in _NEIGHBORS[cur]:
            if nb not in visited and board[nb] == color:
                visited.add(nb)
                queue.append(nb)
    return False


def _all_connected(board: list[int], dots: dict) -> bool:
    """Return True if every color's two dot endpoints are BFS-connected."""
    seen: set[int] = set()
    for cell, color in dots.items():
        if color in seen:
            continue
        seen.add(color)
        endpoints = [c for c, v in dots.items() if v == color]
        if not _color_connected(board, endpoints[0], endpoints[1], color):
            return False
    return True


# ── Game class ────────────────────────────────────────────────────────────────

class FlowFree(Game):
    id        = "flowfree"
    variants  = ["a", "b", "c"]
    n_players = 1
    cyclic    = False

    def __init__(self, variant_id: str):
        if variant_id not in FlowFree.variants:
            raise ValueError(f"Unknown variant '{variant_id}'. Choose from {FlowFree.variants}.")
        self._dots          = PUZZLES[variant_id]
        self._dot_set       = set(self._dots)
        self._non_dot_cells = sorted(set(range(NCELLS)) - self._dot_set)
        n                   = len(self._non_dot_cells)
        self._B_N           = BASE ** n            # weight for active_color
        self._B_N1          = self._B_N * BASE     # weight for active_head
        self._B_N2          = self._B_N1 * (NCELLS + 1)  # weight for starting_dot
        ep: dict[int, list[int]] = {}
        for cell, color in self._dots.items():
            ep.setdefault(color, []).append(cell)
        self._color_endpoints = {c: (cells[0], cells[1]) for c, cells in ep.items()}

    # ── hash / unhash ─────────────────────────────────────────────────────────
    # State = (board, active_color, active_head, starting_dot)
    # starting_dot tracks which endpoint we began drawing from, so we can
    # correctly identify the partner endpoint for path completion.
    # Max hash ≈ 1.9e15, well within SQLite's 64-bit INTEGER range.

    def hash(self, board: list[int], active_color: int,
             active_head: int, starting_dot: int) -> int:
        n = 0
        for i in range(len(self._non_dot_cells) - 1, -1, -1):
            n = n * BASE + board[self._non_dot_cells[i]]
        n += active_color  * self._B_N
        n += active_head   * self._B_N1
        n += starting_dot  * self._B_N2
        return n

    def unhash(self, position: int) -> tuple[list[int], int, int, int]:
        starting_dot = position // self._B_N2
        rest         = position  % self._B_N2
        active_head  = rest // self._B_N1
        rest         = rest  % self._B_N1
        active_color = rest // self._B_N
        rest         = rest  % self._B_N
        board = [0] * NCELLS
        for cell, color in self._dots.items():
            board[cell] = color
        for cell in self._non_dot_cells:
            board[cell] = rest % BASE
            rest //= BASE
        return board, active_color, active_head, starting_dot

    # ── start ─────────────────────────────────────────────────────────────────

    def start(self) -> int:
        board = [0] * NCELLS
        for cell, color in self._dots.items():
            board[cell] = color
        return self.hash(board, 0, NO_HEAD, NO_HEAD)

    # ── generate_moves ────────────────────────────────────────────────────────

    def generate_moves(self, position: int) -> list[int]:
        """
        No active path  ->  tap any dot whose color is not yet connected.
        Active path     ->  tap an adjacent empty cell, or the partner dot
                            (the endpoint that is NOT the starting dot).
        """
        board, active_color, active_head, starting_dot = self.unhash(position)
        moves = []

        if active_color == 0:
            for cell in self._dot_set:
                color = self._dots[cell]
                ep1, ep2 = self._color_endpoints[color]
                if not _color_connected(board, ep1, ep2, color):
                    moves.append(cell)
        else:
            ep1, ep2 = self._color_endpoints[active_color]
            partner = ep2 if starting_dot == ep1 else ep1
            for nb in _NEIGHBORS[active_head]:
                if board[nb] == 0:
                    moves.append(nb)
                elif nb == partner:
                    moves.append(nb)

        return moves

    # ── do_move ───────────────────────────────────────────────────────────────

    def do_move(self, position: int, move: int) -> int:
        board, active_color, active_head, starting_dot = self.unhash(position)

        if active_color == 0:
            new_color = self._dots[move]
            return self.hash(board, new_color, move, move)

        ep1, ep2 = self._color_endpoints[active_color]
        partner = ep2 if starting_dot == ep1 else ep1

        if move == partner:
            board[move] = active_color
            return self.hash(board, 0, NO_HEAD, NO_HEAD)

        board[move] = active_color
        return self.hash(board, active_color, move, starting_dot)

    # ── primitive ─────────────────────────────────────────────────────────────

    def primitive(self, position: int) -> Optional[Value]:
        board, active_color, _, _ = self.unhash(position)
        if active_color != 0:
            return None
        if all(c != 0 for c in board):
            return Value.Win if _all_connected(board, self._dots) else Value.Loss
        return None

    # ── to_string ─────────────────────────────────────────────────────────────

    def to_string(self, position: int, mode: StringMode) -> str:
        board, active_color, active_head, _ = self.unhash(position)

        if mode == StringMode.AUTOGUI:
            cells = "".join(str(c) for c in board)
            return f"{cells}_{active_color}_{active_head}"

        lines = ["  0 1 2 3 4"]
        for r in range(SIZE):
            row = f"{r} "
            for c in range(SIZE):
                idx = r * SIZE + c
                ch  = COLOR_NAMES[board[idx]]
                if active_color != 0 and idx == active_head:
                    ch = ch.lower()
                row += ch + " "
            lines.append(row.rstrip())
        head_label   = str(active_head) if active_color != 0 else "-"
        active_label = COLOR_NAMES.get(active_color, "?")
        lines.append(f"Drawing: {active_label}   Head: {head_label}")
        return "\n".join(lines)

    # ── from_string ───────────────────────────────────────────────────────────

    def from_string(self, strposition: str) -> int:
        parts = strposition.strip().split("_")
        if len(parts) != 3:
            raise ValueError(f"Expected '<cells>_<color>_<head>', got: {strposition!r}")
        cells_str, ac_str, ah_str = parts
        if len(cells_str) != NCELLS:
            raise ValueError(f"Expected {NCELLS} digits, got {len(cells_str)}")
        # starting_dot not stored in string; infer it as NO_HEAD (rest states only)
        return self.hash([int(ch) for ch in cells_str], int(ac_str), int(ah_str), NO_HEAD)

    # ── move_to_string ────────────────────────────────────────────────────────

    def move_to_string(self, move: int, mode: StringMode) -> str:
        if mode == StringMode.AUTOGUI:
            return str(move)
        r, c = divmod(move, SIZE)
        return f"{r},{c}"
