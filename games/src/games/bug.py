from models import Game, Value, StringMode # type: ignore
from typing import Optional

"""
Position (int): an optional leading 1 (= player 1 to move; no leading digit = player 2 to move)
followed by 19 cell digits: 0 = empty, 1 = player 1 (W), 2 = player 2 (B).
Cell i (tile number i+1, reading order: left to right, top row first) is the i-th digit
from the RIGHT, so the last digit is tile 1 (row+column 11) and the first cell digit is tile 19 (53).

Move (int): the moving player's digit followed by two-digit tile numbers (01-19):
the placement first, then each growth in the order it happens.
e.g. 2140915 = player 2 places on tile 14, then grows onto tile 9, then onto tile 15.

Eating is resolved in a fixed order: after placing, the eater is always the player's bug
with the lowest-numbered cell (numbered on the board turned to its standard orientation,
see canonical(), so that rotated/mirrored boards play identically) that (a) touches an enemy bug of the same shape (rotations and
reflections allowed) and (b) still has a legal growth cell once those enemy bugs are removed.
It eats every such enemy bug next to it, then grows by one cell (each possible cell is a
separate move). This repeats until none of the player's bugs can eat.
"""

ROWS = [3, 4, 5, 4, 3]
N = 19
FULL = (1 << N) - 1

# axial coordinates (official x:y labels) of each cell, in tile order
COORDS = [(x, y) for y, n in enumerate(ROWS) for x in range(max(0, 2 - y), max(0, 2 - y) + n)]
INDEX = {c: i for i, c in enumerate(COORDS)}
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]

# NBR[i] = bitmask of the cells next to cell i
NBR = [sum(1 << INDEX[(x + dx, y + dy)] for dx, dy in DIRS if (x + dx, y + dy) in INDEX)
       for (x, y) in COORDS]

def _rot(p):   # 60 degree rotation about the origin in axial coordinates
    return (-p[1], p[0] + p[1])

def _refl(p):  # mirror
    return (p[1], p[0])

def _transforms():
    out = []
    for mirror in (False, True):
        for r in range(6):
            def f(p, mirror=mirror, r=r):
                if mirror:
                    p = _refl(p)
                for _ in range(r):
                    p = _rot(p)
                return p
            out.append(f)
    return out
TRANSFORMS = _transforms()

# the 12 symmetries of the board as cell permutations, and lookup tables that apply a
# permutation to a whole bitmask (low 10 bits and high 9 bits looked up separately)
_CENTER = (2, 2)
def _board_perm(f):
    perm = []
    for (x, y) in COORDS:
        p = f((x - _CENTER[0], y - _CENTER[1]))
        perm.append(INDEX[(p[0] + _CENTER[0], p[1] + _CENTER[1])])
    return perm
SYM_PERMS = [_board_perm(f) for f in TRANSFORMS]

def _perm_tables(perm):
    lo = [0] * 1024
    hi = [0] * 512
    for m in range(1024):
        v = 0
        for i in range(10):
            if m >> i & 1:
                v |= 1 << perm[i]
        lo[m] = v
    for m in range(512):
        v = 0
        for i in range(9):
            if m >> i & 1:
                v |= 1 << perm[i + 10]
        hi[m] = v
    return lo, hi
SYM_TABLES = [_perm_tables(p) for p in SYM_PERMS]
INV_PERMS = [[perm.index(i) for i in range(N)] for perm in SYM_PERMS]
INV_TABLES = [_perm_tables(p) for p in INV_PERMS]

def canonical(w: int, b: int) -> tuple[int, int, int]:
    """Standard orientation of a board: (symmetry index, player 1 mask, player 2 mask)."""
    best = None
    for t, (lo, hi) in enumerate(SYM_TABLES):
        key = (lo[w & 1023] | hi[w >> 10], lo[b & 1023] | hi[b >> 10], t)
        if best is None or key < best:
            best = key
    return best[2], best[0], best[1]  # type: ignore

# base-3 value of a bitmask of cells (cell i has weight 3**i), in two lookup halves
POW3_LO = [sum(3**i for i in range(10) if m >> i & 1) for m in range(1024)]
POW3_HI = [sum(3**(i + 10) for i in range(9) if m >> i & 1) for m in range(512)]

def unmap(t: int, mask: int) -> int:
    """Undo symmetry t on a bitmask."""
    lo, hi = INV_TABLES[t]
    return lo[mask & 1023] | hi[mask >> 10]

_shape_cache: dict[int, tuple] = {}
def shape_of(mask: int) -> tuple:
    """Canonical shape of a set of cells, the same for all translations, rotations and reflections."""
    s = _shape_cache.get(mask)
    if s is None:
        pts = [COORDS[i] for i in range(N) if mask >> i & 1]
        best = None
        for f in TRANSFORMS:
            q = sorted(f(p) for p in pts)
            ox, oy = q[0]
            cand = tuple((a - ox, b - oy) for a, b in q)
            if best is None or cand < best:
                best = cand
        s = _shape_cache[mask] = best  # type: ignore
    return s

_nbr_cache: dict[int, int] = {}
def around(mask: int) -> int:
    """Bitmask of the cells next to mask (not including mask itself)."""
    r = _nbr_cache.get(mask)
    if r is None:
        r = 0
        m = mask
        while m:
            b = m & -m
            r |= NBR[b.bit_length() - 1]
            m ^= b
        r &= ~mask
        _nbr_cache[mask] = r
    return r

def bugs_of(mask: int) -> list[int]:
    """Connected groups of cells in mask, ordered by their lowest cell."""
    out = []
    while mask:
        comp = frontier = mask & -mask
        while frontier:
            new = around(frontier) & mask & ~comp
            comp |= new
            frontier = new
        out.append(comp)
        mask &= ~comp
    return out

def decode(position: int) -> tuple[int, int, int]:
    """position -> (player to move, player 1 mask, player 2 mask)"""
    s = str(position)
    if len(s) == 20:
        player, s = 1, s[1:]
    else:
        player, s = 2, s.zfill(19)
    # the leftmost digit is cell 18, so the string reads directly as a binary number
    return player, int(s.replace('2', '0'), 2), int(s.replace('1', '0').replace('2', '1'), 2)

def encode(player: int, w: int, b: int) -> int:
    """(player to move, player 1 mask, player 2 mask) -> position"""
    v = int(format(w, 'b')) + 2 * int(format(b, 'b'))
    return v + 10**19 if player == 1 else v

def placements(own: int, opp: int) -> list[int]:
    """Cells the player may place on: empty, not touching two of their own bugs, and not growing
    a bug beyond the largest bug on the board."""
    own_bugs = bugs_of(own)
    all_bugs = own_bugs + bugs_of(opp)
    maxsize = max((g.bit_count() for g in all_bugs), default=0)
    empty = FULL & ~(own | opp)
    out = []
    for c in range(N):
        if not empty >> c & 1:
            continue
        touching = [g for g in own_bugs if NBR[c] & g]
        if len(touching) > 1:
            continue
        if touching and touching[0].bit_count() >= maxsize:
            continue
        out.append(c)
    return out

def next_eater(own: int, opp: int):
    """The bug that eats next under the fixed order, or None.
    Returns (eater mask, removed enemy cells, growth cells mask)."""
    opp_bugs = None
    for g in bugs_of(own):
        near = around(g) & opp
        if not near:
            continue
        if opp_bugs is None:
            opp_bugs = bugs_of(opp)
        size = g.bit_count()
        shape = None
        removed = 0
        for e in opp_bugs:
            if e & near and e.bit_count() == size:
                if shape is None:
                    shape = shape_of(g)
                if shape_of(e) == shape:
                    removed |= e
        if not removed:
            continue
        empty = FULL & ~(own | opp) | removed
        others = own & ~g
        spots = 0
        cand = around(g) & empty
        while cand:
            b = cand & -cand
            c = b.bit_length() - 1
            if not NBR[c] & others:
                spots |= b
            cand ^= b
        if spots:
            return g, removed, spots
    return None

def resolve(own: int, opp: int, tiles: list[int], out: list):
    """Play out the eating chain after a placement, branching on growth cells.
    Appends (own, opp, tiles) for every way the turn can end."""
    eat = next_eater(own, opp)
    if eat is None:
        out.append((own, opp, tiles))
        return
    _, removed, spots = eat
    opp2 = opp & ~removed
    while spots:
        b = spots & -spots
        resolve(own | b, opp2, tiles + [b.bit_length() - 1], out)
        spots ^= b

class Bug(Game):
    id = 'bug'
    variants = ["regular", "test"]
    n_players = 2
    cyclic = False

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Bug.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        # PERF: children of the last position generated, so the solver's
        # primitive() -> generate_moves() -> do_move() calls reuse one computation
        self._cache_pos = None
        self._cache_moves: list[int] = []
        self._cache_children: dict[int, int] = {}

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return 10**19 # 1 and 19 zeros

    def _expand(self, position: int):
        if position == self._cache_pos:
            return
        player, w, b = decode(position)
        # work on the board in its standard orientation, then map the results back
        t, cw, cb = canonical(w, b)
        inv = INV_PERMS[t]
        own, opp = (cw, cb) if player == 1 else (cb, cw)
        ends = []
        for c in placements(own, opp):
            resolve(own | 1 << c, opp, [c], ends)
        children: dict[int, int] = {}
        seen = set()
        moves = []
        for o, p, tiles in ends:
            o, p, tiles = unmap(t, o), unmap(t, p), [inv[c] for c in tiles]
            child = encode(2, o, p) if player == 1 else encode(1, p, o)
            if child in seen:   # different growth orders that end in the same board
                continue
            seen.add(child)
            move = int(str(player) + "".join(f"{t + 1:02d}" for t in tiles))
            moves.append(move)
            children[move] = child
        self._cache_pos = position
        self._cache_moves = moves
        self._cache_children = children

    def generate_moves(self, position: int) -> list[int]:
        """
        Returns the list of legal moves from the input position.
        """
        self._expand(position)
        return list(self._cache_moves)

    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        if position == self._cache_pos and move in self._cache_children:
            return self._cache_children[move]
        player, w, b = decode(position)
        own, opp, _ = self._replay(position, move)
        return encode(2, own, opp) if player == 1 else encode(1, opp, own)

    def _replay(self, position: int, move: int):
        """Apply a move tile by tile. Returns (own, opp, changes) where changes lists
        (cell, new value) in the order they happen."""
        player, w, b = decode(position)
        t, cw, cb = canonical(w, b)
        perm, inv = SYM_PERMS[t], INV_PERMS[t]
        own, opp = (cw, cb) if player == 1 else (cb, cw)
        s = str(move)
        if int(s[0]) != player:
            raise ValueError(f"move {move} is for player {s[0]}, but player {player} is to move")
        tiles = [perm[int(s[i:i + 2]) - 1] for i in range(1, len(s), 2)]
        changes = [(tiles[0], player)]
        own |= 1 << tiles[0]
        for g in tiles[1:]:
            eat = next_eater(own, opp)
            if eat is None or not eat[2] >> g & 1:
                raise ValueError(f"move {move} is not legal from position {position}")
            _, removed, _ = eat
            changes += [(c, 0) for c in range(N) if removed >> c & 1]
            opp &= ~removed
            own |= 1 << g
            changes.append((g, player))
        if next_eater(own, opp) is not None:
            raise ValueError(f"move {move} stops before the eating chain is finished")
        return unmap(t, own), unmap(t, opp), [(inv[c], v) for c, v in changes]

    def unpack(self, position: int, move: int) -> str:
        """
        Unpacks a move into every tile it changes: value digit + row+column ID per change,
        e.g. '242' + '012' = tile 42 becomes player 2, tile 12 is eaten.
        """
        _, _, changes = self._replay(position, move)
        return "".join(f"{v}{self.LABELS[c]}" for c, v in changes)

    def hash_ext(self, position: int) -> int:
        """
        PERF: map every position to one canonical member of its symmetry class
        (6 rotations x 2 reflections) so symmetric positions are solved only once.
        Returns a compact database key: the 19 cell digits (standard orientation) read as a
        base-3 number, times 2, plus 1 if it is player 1's turn. Always below 2.4 billion, so it
        fits in a SQLite INTEGER (a raw position can be up to 1.2 * 10^19, which does not).
        """
        player, w, b = decode(position)
        _, cw, cb = canonical(w, b)
        board = POW3_LO[cw & 1023] + POW3_HI[cw >> 10] + 2 * (POW3_LO[cb & 1023] + POW3_HI[cb >> 10])
        return board * 2 + (player == 1)

    def unhash_ext(self, hashed_pos: int) -> int:
        """
        Turns a database key from hash_ext back into a position (in standard orientation).
        """
        board, player1 = divmod(hashed_pos, 2)
        w = b = 0
        for i in range(N):
            board, d = divmod(board, 3)
            if d == 1:
                w |= 1 << i
            elif d == 2:
                b |= 1 << i
        return encode(1 if player1 else 2, w, b)

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal.
        A player who cannot place on their turn wins.
        """
        if not self.generate_moves(position):
            return Value.Win
        return None
    
    ROWS = [3, 4, 5, 4, 3]
    FILL = {'0': '🟡', '1': '⚪', '2': '⚫'}
    # LABELS[i] is the row+column ID of Board.spaces[i] (rows 1-5 top to bottom,
    # columns counted from 1 at the left of each row), same as TILE_IDS in unpack
    LABELS = [f"{r}{c}" for r, n in enumerate(ROWS, 1) for c in range(1, n + 1)]

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        if mode != StringMode.TUI:
                return str(position)
        digits = str(position).zfill(20)[-19:][::-1]
        P, H = 10, 4
        edge = "'-._____.-"
        canvas = [[' '] * (P * 5 + 1) for _ in range(H * 5 + 1)]
        t = 0
        for r, n in enumerate(self.ROWS):
            y, x0 = r * H, (5 - n) * P // 2
            for c in range(n):
                x = x0 + c * P
                e = [self.FILL[digits[t]], '']      # one emoji = 2 columns
                solid = ['|'] + e*2 + [' '] + e*2 + ['|']
                label = ['|'] + e + list(f" {self.LABELS[t]:^3} ") + e + ['|']
                canvas[y+1][x:x+P+1] = solid
                canvas[y+2][x:x+P+1] = label
                canvas[y+3][x:x+P+1] = solid
                cx = x + P // 2
                for i in range(P + 1):
                    canvas[y][x+i]   = edge[(x + i - cx) % P]
                    canvas[y+H][x+i] = edge[(x + i - cx + P//2) % P]
                t += 1

        currentPlayer = 'BLACK ⚫' if len(str(position)) <20 else 'WHITE ⚪'

        return "\n".join("".join(row).rstrip() for row in canvas) + f'\n\n Current player: {currentPlayer} \n'

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        return int(strposition)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        if mode != StringMode.TUI:
            return str(move)
        s = str(move)[1:]                     # drop the player digit
        return " ".join(self.LABELS[int(s[i:i+2]) - 1] for i in range(0, len(s), 2))