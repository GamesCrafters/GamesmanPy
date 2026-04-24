"""
Whole Year Puzzle — GamesmanPy Implementation with AUTOGUI Support

A 1-player puzzle where 9 distinct polyomino pieces must tile a shaped 7×7
board, leaving exactly two cells uncovered: one for the target month and one
for the target day.

Board layout (43 valid cells):
  Row 0: cols 0-5  → Jan … Jun
  Row 1: cols 0-5  → Jul … Dec
  Rows 2-5: cols 0-6 → days 1-28
  Row 6: cols 2-4  → days 29-31

Position encoding (Python int):
  bits [0..8]   = used_pieces bitmask  (which of the 9 pieces are placed)
  bits [9..49]  = covered bitmask      (which playable cells are occupied)

Move encoding (Python int):
  bits [0..2]  = anchor column  (0-6)
  bits [3..5]  = anchor row     (0-6)
  bits [6..8]  = orientation    (0-7)
  bits [9..12] = piece index    (0-8)
"""

from models import Game, Value, StringMode
from typing import Optional

# ───────────────────────── Board Geometry ─────────────────────────

ROWS, COLS = 7, 7
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

VALID_CELLS: set[tuple[int, int]] = set()
CELL_LABELS: dict[tuple[int, int], str] = {}

# Ordered list of all 43 valid cells (row-major), used for AUTOGUI indexing
VALID_CELLS_ORDERED: list[tuple[int, int]] = []
VALID_CELL_TO_IDX: dict[tuple[int, int], int] = {}


def _init_board():
    for c in range(6):
        VALID_CELLS.add((0, c))
        CELL_LABELS[(0, c)] = MONTHS[c]
    for c in range(6):
        VALID_CELLS.add((1, c))
        CELL_LABELS[(1, c)] = MONTHS[6 + c]
    for r in range(2, 6):
        for c in range(7):
            VALID_CELLS.add((r, c))
            CELL_LABELS[(r, c)] = str((r - 2) * 7 + c + 1)
    for c in range(2, 5):
        VALID_CELLS.add((6, c))
        CELL_LABELS[(6, c)] = str(29 + c - 2)
    # Build ordered list (row-major)
    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) in VALID_CELLS:
                idx = len(VALID_CELLS_ORDERED)
                VALID_CELLS_ORDERED.append((r, c))
                VALID_CELL_TO_IDX[(r, c)] = idx


_init_board()
assert len(VALID_CELLS_ORDERED) == 43

# ───────────────────────── Piece Definitions ─────────────────────

PIECES = [
    [(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)],  # A  5 cells
    [(0, 0), (0, 1), (1, 0), (1, 1)],            # B  4 cells
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],    # C  5 cells
    [(0, 0), (1, 0), (1, 1), (2, 1)],            # D  4 cells
    [(0, 0), (1, 0), (1, 1), (2, 0)],            # E  4 cells
    [(0, 0), (0, 1), (1, 0), (2, 0)],            # F  4 cells
    [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2)],    # G  5 cells
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)],    # H  5 cells
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],    # I  5 cells
]
PIECE_SYMS = list("ABCDEFGHI")
NUM_PIECES = 9


# ───────────────────── Orientation Helpers ───────────────────────

def _rotate_cw(cells):
    rot = [(c, -r) for r, c in cells]
    mr = min(r for r, _ in rot)
    mc = min(c for _, c in rot)
    return sorted((r - mr, c - mc) for r, c in rot)


def _flip_h(cells):
    mx = max(c for _, c in cells)
    f = [(r, mx - c) for r, c in cells]
    mc = min(c for _, c in f)
    return sorted((r, c - mc) for r, c in f)


def _all_orientations(cells):
    seen: set[tuple] = set()
    results = []
    cur = sorted(cells)
    for _ in range(4):
        for variant in (cur, _flip_h(cur)):
            key = tuple(variant)
            if key not in seen:
                seen.add(key)
                results.append(list(variant))
        cur = _rotate_cw(cur)
    return results


ALL_ORI = [_all_orientations(p) for p in PIECES]

# ───────────────────────── Game Class ────────────────────────────


class WholeYearPuzzle(Game):
    id = "wholeyearpuzzle"
    name = "Whole Year Puzzle"
    n_players = 1
    cyclic = False
    uses_half_moves = True

    # Half-move type tags (bits 13-14 of half-move int)
    _HM_PIECE  = 1      # select a piece
    _HM_ORI    = 2      # select an orientation
    _HM_ANCHOR = 3      # select anchor = complete move

    # Half-position layout: real_pos in bits [0..49],
    # sel_piece+1 in bits [50..53], sel_ori+1 in bits [54..57]
    _HP_PIECE_SHIFT = 50
    _HP_ORI_SHIFT   = 54

    # 366 variants: "1-1" through "12-31"
    variants = [
        f"{m}-{d}"
        for m in range(1, 13)
        for d in range(1, DAYS_IN_MONTH[m - 1] + 1)
    ]

    def __init__(self, variant_id: str):
        if variant_id not in WholeYearPuzzle.variants:
            raise ValueError(f"Invalid variant: {variant_id}")
        self._variant_id = variant_id
        month_str, day_str = variant_id.split("-")
        self.month = int(month_str)
        self.day = int(day_str)

        self.targets = self._compute_targets()
        self.target_set = frozenset(self.targets)

        self.playable = sorted(
            c for c in VALID_CELLS if c not in self.target_set
        )
        self.playable_set = frozenset(self.playable)
        self.playable_to_idx = {cell: i for i, cell in enumerate(self.playable)}
        self.num_playable = len(self.playable)  # 41

        self._placements = self._precompute_placements()

    def _compute_targets(self) -> list[tuple[int, int]]:
        t: list[tuple[int, int]] = []
        m = self.month - 1
        t.append((0, m) if m < 6 else (1, m - 6))
        d = self.day
        t.append(((d - 1) // 7 + 2, (d - 1) % 7) if d <= 28 else (6, d - 27))
        return t

    def _precompute_placements(self) -> list[list[tuple[int, int, int, int]]]:
        result: list[list[tuple[int, int, int, int]]] = []
        for pi in range(NUM_PIECES):
            placements: list[tuple[int, int, int, int]] = []
            for oi, shape in enumerate(ALL_ORI[pi]):
                for r in range(ROWS):
                    for c in range(COLS):
                        bitmask = 0
                        ok = True
                        for dr, dc in shape:
                            nr, nc = r + dr, c + dc
                            if (nr, nc) not in self.playable_set:
                                ok = False
                                break
                            bitmask |= 1 << self.playable_to_idx[(nr, nc)]
                        if ok:
                            placements.append((oi, r, c, bitmask))
            result.append(placements)
        return result

    # ── GamesmanPy interface ──────────────────────────────────────

    def start(self) -> int:
        return 0

    def generate_moves(self, position: int) -> list[int]:
        used = position & 0x1FF
        covered = position >> NUM_PIECES
        moves: list[int] = []
        for pi in range(NUM_PIECES):
            if used & (1 << pi):
                continue
            for oi, r, c, mask in self._placements[pi]:
                if covered & mask:
                    continue
                moves.append((pi << 9) | (oi << 6) | (r << 3) | c)
            break  # canonical: first unused piece only
        return moves

    def do_move(self, position: int, move: int) -> int:
        pi = (move >> 9) & 0xF
        oi = (move >> 6) & 0x7
        r = (move >> 3) & 0x7
        c = move & 0x7

        used = position & 0x1FF
        covered = position >> NUM_PIECES

        mask = 0
        for dr, dc in ALL_ORI[pi][oi]:
            mask |= 1 << self.playable_to_idx[(r + dr, c + dc)]

        return ((covered | mask) << NUM_PIECES) | (used | (1 << pi))

    def primitive(self, position: int) -> Optional[Value]:
        real_pos = self._real_pos(position)
        if (real_pos & 0x1FF) == 0x1FF:
            return Value.Win
        return None

    def move_to_string(self, move: int, mode: StringMode) -> str:
        # Dispatch half-moves (bits 13-14 set) to half_move_to_string
        if (move >> 13) & 0x3:
            return self.half_move_to_string(move, mode)

        pi = (move >> 9) & 0xF
        oi = (move >> 6) & 0x7
        r = (move >> 3) & 0x7
        c = move & 0x7

        if mode == StringMode.AUTOGUI:
            # Find the smallest valid-cell index covered by this placement
            cells = [(r + dr, c + dc) for dr, dc in ALL_ORI[pi][oi]]
            min_vidx = min(VALID_CELL_TO_IDX[cell] for cell in cells)
            # A-type: token=piece letter, center=min cell index
            # Append _<ori> to disambiguate overlapping placements
            return f"A_{PIECE_SYMS[pi]}_{min_vidx}_{oi}"

        # Readable
        cells = [(r + dr, c + dc) for dr, dc in ALL_ORI[pi][oi]]
        labels = [
            CELL_LABELS.get(cell, f"({cell[0]},{cell[1]})")
            for cell in cells
        ]
        return f"Place {PIECE_SYMS[pi]} (orient {oi}) -> [{', '.join(labels)}]"

    # ── Half-position helpers ────────────────────────────────────

    def _real_pos(self, half_pos: int) -> int:
        return half_pos & ((1 << self._HP_PIECE_SHIFT) - 1)

    def _sel_piece(self, half_pos: int) -> Optional[int]:
        v = (half_pos >> self._HP_PIECE_SHIFT) & 0xF
        return v - 1 if v > 0 else None

    def _sel_ori(self, half_pos: int) -> Optional[int]:
        v = (half_pos >> self._HP_ORI_SHIFT) & 0xF
        return v - 1 if v > 0 else None

    def _make_half_pos(self, real_pos: int,
                       sel_piece: Optional[int] = None,
                       sel_ori: Optional[int] = None) -> int:
        hp = real_pos
        if sel_piece is not None:
            hp |= (sel_piece + 1) << self._HP_PIECE_SHIFT
        if sel_ori is not None:
            hp |= (sel_ori + 1) << self._HP_ORI_SHIFT
        return hp

    # ── Half-move encoding helpers ───────────────────────────────

    @staticmethod
    def _hm_type(half_move: int) -> int:
        return (half_move >> 13) & 0x3

    @staticmethod
    def _make_hm_piece(pi: int) -> int:
        return (WholeYearPuzzle._HM_PIECE << 13) | (pi << 9)

    @staticmethod
    def _make_hm_ori(pi: int, oi: int) -> int:
        return (WholeYearPuzzle._HM_ORI << 13) | (pi << 9) | (oi << 6)

    @staticmethod
    def _make_hm_anchor(pi: int, oi: int, r: int, c: int) -> int:
        return (WholeYearPuzzle._HM_ANCHOR << 13) | (pi << 9) | (oi << 6) | (r << 3) | c

    # ── GamesmanPy half-move interface ───────────────────────────

    def generate_half_moves(self, position: int) -> list[int]:
        sel_pi = self._sel_piece(position)
        sel_oi = self._sel_ori(position)
        real_pos = self._real_pos(position)
        used = real_pos & 0x1FF
        covered = real_pos >> NUM_PIECES

        if sel_pi is None:
            # Step 1: offer each unused piece
            moves = []
            for pi in range(NUM_PIECES):
                if used & (1 << pi):
                    continue
                if any(not (covered & mask) for _, _, _, mask in self._placements[pi]):
                    moves.append(self._make_hm_piece(pi))
            return moves

        if sel_oi is None:
            # Step 2: offer each orientation of the selected piece that has
            # at least one valid anchor on the current board
            seen_oris: set[int] = set()
            moves = []
            for oi, _, _, mask in self._placements[sel_pi]:
                if oi in seen_oris:
                    continue
                if not (covered & mask):
                    seen_oris.add(oi)
                    moves.append(self._make_hm_ori(sel_pi, oi))
            return moves

        # Step 3: offer each valid anchor for (piece, orientation)
        moves = []
        for oi, r, c, mask in self._placements[sel_pi]:
            if oi != sel_oi:
                continue
            if covered & mask:
                continue
            moves.append(self._make_hm_anchor(sel_pi, sel_oi, r, c))
        return moves

    def do_half_move(self, position: int, half_move: int,
                     move_dict: dict[int, tuple[int, Value]]):
        """
        Returns (new_half_pos, half_move_val, half_pos_rem, half_pos_val).

        For intermediate steps (select piece / select orientation):
          - new_half_pos is a half-position with sel_piece / sel_ori set
          - half_move_val / half_pos_val = best value reachable via this choice
          - half_pos_rem = best remoteness reachable via this choice

        For the final step (select anchor):
          - new_half_pos is the real child position (no half-state)
          - values come directly from move_dict
        """
        real_pos = self._real_pos(position)
        hm_type = self._hm_type(half_move)
        pi = (half_move >> 9) & 0xF

        if hm_type == self._HM_PIECE:
            # Intermediate: pick the best (val, rem) among all full moves
            # starting with this piece
            new_hp = self._make_half_pos(real_pos, sel_piece=pi)
            best_val, best_rem = self._best_among_piece(pi, None, real_pos, move_dict)
            return (new_hp, best_val, best_rem, best_val)

        oi = (half_move >> 6) & 0x7

        if hm_type == self._HM_ORI:
            # Intermediate: pick the best among all full moves with (pi, oi)
            new_hp = self._make_half_pos(real_pos, sel_piece=pi, sel_ori=oi)
            best_val, best_rem = self._best_among_piece(pi, oi, real_pos, move_dict)
            return (new_hp, best_val, best_rem, best_val)

        # hm_type == _HM_ANCHOR → complete move
        r = (half_move >> 3) & 0x7
        c = half_move & 0x7
        full_move = (pi << 9) | (oi << 6) | (r << 3) | c
        child_pos = self.do_move(real_pos, full_move)
        child_hash = self.hash_ext(child_pos)

        if full_move in move_dict:
            child_rem, child_val = move_dict[full_move]
        else:
            child_rem, child_val = 0, Value.Win if self.primitive(child_pos) == Value.Win else Value.Loss

        return (child_pos, child_val, child_rem, child_val)

    def _best_among_piece(self, pi: int, oi: Optional[int],
                          real_pos: int,
                          move_dict: dict) -> tuple[Value, int]:
        """Find the best (val, rem) among all full moves matching (pi, oi)."""
        used = real_pos & 0x1FF
        covered = real_pos >> NUM_PIECES
        best_val = Value.Loss
        best_rem = 0

        for o, r, c, mask in self._placements[pi]:
            if oi is not None and o != oi:
                continue
            if covered & mask:
                continue
            full_move = (pi << 9) | (o << 6) | (r << 3) | c
            child_pos = self.do_move(real_pos, full_move)
            child_hash = self.hash_ext(child_pos)

            entry = move_dict.get(full_move)
            if entry is None:
                continue
            c_rem, c_val = entry

            if c_val > best_val or (c_val == best_val and c_val == Value.Win and c_rem < best_rem):
                best_val = c_val
                best_rem = c_rem

        return (best_val, best_rem)

    # ── Half-move string conversions ─────────────────────────────

    def half_move_to_string(self, half_move: int, mode: StringMode) -> str:
        hm_type = self._hm_type(half_move)
        pi = (half_move >> 9) & 0xF

        if hm_type == self._HM_PIECE:
            if mode == StringMode.AUTOGUI:
                return f"A_{PIECE_SYMS[pi]}_s"
            return f"Select piece {PIECE_SYMS[pi]}"

        oi = (half_move >> 6) & 0x7

        if hm_type == self._HM_ORI:
            if mode == StringMode.AUTOGUI:
                return f"A_{PIECE_SYMS[pi]}{oi}_o"
            return f"Select {PIECE_SYMS[pi]} orientation {oi}"

        # _HM_ANCHOR — same as full move_to_string
        return self.move_to_string(half_move & 0x1FFF, mode)

    # ── Half-position string conversions ─────────────────────────

    def to_string(self, position: int, mode: StringMode) -> str:
        real_pos = self._real_pos(position)
        sel_pi = self._sel_piece(position)
        sel_oi = self._sel_ori(position)

        used = real_pos & 0x1FF
        covered = real_pos >> NUM_PIECES

        board_chars = []
        for cell in VALID_CELLS_ORDERED:
            if cell in self.target_set:
                board_chars.append('T')
            elif cell in self.playable_set:
                idx = self.playable_to_idx[cell]
                board_chars.append('X' if (covered & (1 << idx)) else '-')
            else:
                board_chars.append('-')
        board_str = ''.join(board_chars)

        if mode == StringMode.AUTOGUI:
            suffix = ""
            if sel_pi is not None:
                suffix += f"_{PIECE_SYMS[sel_pi]}"
                if sel_oi is not None:
                    suffix += f"{sel_oi}"
            return f"1_{board_str}{suffix}"

        pieces_str = ''.join(
            '1' if (used & (1 << pi)) else '0'
            for pi in range(NUM_PIECES)
        )
        suffix = ""
        if sel_pi is not None:
            suffix += f"_{PIECE_SYMS[sel_pi]}"
            if sel_oi is not None:
                suffix += f"{sel_oi}"
        return f"1_{board_str}_{pieces_str}{suffix}"

    def from_string(self, strposition: str) -> int:
        parts = strposition.split("_")
        board_str = parts[1]

        # Parse optional piece bits (part 2) and half-state suffix
        pieces_str = None
        sel_piece_str = None

        if len(parts) >= 3:
            p2 = parts[2]
            if len(p2) == NUM_PIECES and all(ch in '01' for ch in p2):
                pieces_str = p2
                if len(parts) >= 4:
                    sel_piece_str = parts[3]
            else:
                sel_piece_str = p2

        covered = 0
        for cell in VALID_CELLS_ORDERED:
            if cell in self.playable_set:
                idx = self.playable_to_idx[cell]
                vidx = VALID_CELL_TO_IDX[cell]
                if board_str[vidx] == 'X':
                    covered |= 1 << idx

        used = 0
        if pieces_str:
            for i, ch in enumerate(pieces_str):
                if ch == '1':
                    used |= 1 << i
        else:
            n_covered = bin(covered).count('1')
            total = 0
            for pi in range(NUM_PIECES):
                piece_size = len(PIECES[pi])
                if total + piece_size <= n_covered:
                    used |= 1 << pi
                    total += piece_size

        real_pos = (covered << NUM_PIECES) | used

        sel_pi = None
        sel_oi = None
        if sel_piece_str:
            sel_pi = PIECE_SYMS.index(sel_piece_str[0])
            if len(sel_piece_str) > 1:
                sel_oi = int(sel_piece_str[1])

        return self._make_half_pos(real_pos, sel_pi, sel_oi)
