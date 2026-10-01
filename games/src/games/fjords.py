import random
from typing import Optional

from models import Game, Value, StringMode


class Fjords(Game):
    """
    Second phase of Fjords (Grail Games): a triangular-grid board is seeded
    with a few Blue/Red vertices left over from the (unmodeled) first
    phase. On your turn you color any uncolored vertex adjacent to a vertex
    of your own color. Blue moves first; a player with no legal move loses
    (normal play convention, no ties).

    `self.board` is a fixed adjacency list, one entry per vertex:
    `self.board[i] = [color, [neighbor_indices...]]`, where `color` is
    0 (uncolored), 1 (Blue), or 2 (Red). Seeded (already-colored) vertices
    never change, so `position` only needs to encode the vertices that
    started uncolored -- `self._mutable_indices` lists those board indices
    in row-major order, and a "move"/digit index is an index into that
    list, not a raw board index.

    The "regular" variant is a hand-transcribed copy of the assignment's
    reference board (25 vertices, 8 pre-colored seeds). "board2" generates
    a random board of the same size using the same
    edge-carving/seed-placement algorithm as the kyleburke.info JS
    reference (see `_generate_random_board` and helpers below), with a
    fixed seed so it's reproducible.
    """

    id = 'fjords'
    variants = ["regular", "board2"]
    n_players = 2
    cyclic = False

    _UNCOLORED = 0b00
    _BLUE = 0b01
    _RED = 0b10

    # Hand-transcribed from the assignment's reference board screenshot:
    # 25 vertices (5x5, row-major), 8 pre-colored Blue/Red seeds.
    _REGULAR_BOARD = [
        [0, [5, 6]], [0, [2]], [2, [1, 7, 8, 3]], [0, [2, 4, 8, 9]], [0, [3]],
        [0, [0]], [1, [0, 10, 11]], [0, [2, 8, 11, 12]], [1, [2, 3, 7, 13]], [1, [3, 13, 14]],
        [0, [6, 11, 15, 16]], [0, [6, 7, 10, 12, 16]], [0, [7, 11, 13]], [2, [8, 9, 12]], [0, [9]],
        [0, [10, 20]], [2, [10, 11, 17, 20, 21]], [0, [16, 18, 22]], [0, [17, 19]], [0, [18, 23]],
        [0, [15, 16, 21]], [0, [16, 20, 22]], [1, [17, 21]], [2, [19, 24]], [0, [23]],
    ]
    _BOARD_2 = [
        [0, [6]], [1, [2]], [2, [1,3,7,8]], [0, [2,4,8,9]], [0,[3]],
        [0,[6]], [0, [0,5,7]], [0,[2,6,8,12]], [0,[2,3,7,9,12,13]], [0,[3,13]],
        [1,[11,16]], [0,[10,12,17]],[0,[7,8,11,17]],[0,[8,9,14,18]],[2,[13,19]],
        [0,[20]],[0,[10,20,21]],[1,[11,12,18]],[2,[13,17,19,23]],[1,[14,18,23]],
        [0,[15,16]],[0,[16,22]],[0,[21]],[2,[18,19,24]],[0,[23]]
    ]

    def __init__(self, variant_id: str):
        if variant_id not in Fjords.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self.b_width = 5
        self.b_length = 5
        self.board=None

        if variant_id == "regular":
            self.board = [[color, list(neighbors)] for color, neighbors in self._REGULAR_BOARD]
        else:
            self.board = [[color, list(neighbors)] for color, neighbors in self._BOARD_2]
        self._mutable_indices = [
            i for i, (color, _) in enumerate(self.board) if color == self._UNCOLORED
        ]
        self._board_index_to_digit = {
            board_index: digit for digit, board_index in enumerate(self._mutable_indices)
        }
        self._n_digits = len(self._mutable_indices)

    # -- Game contract --------------------------------------------------

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return 0

    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        digits = self._unpack(position)
        effective = self._effective_colors(digits)
        turn = self._turn_code(digits)
        moves = set()
        for vertex, color in enumerate(effective):
            if color != turn:
                continue
            for neighbor in self.board[vertex][1]:
                if effective[neighbor] == self._UNCOLORED:
                    moves.add(self._board_index_to_digit[neighbor])
        return sorted(moves)

    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        digits = self._unpack(position)
        turn = self._turn_code(digits)
        digits[move] = turn
        return self._pack(digits)

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
        digits = self._unpack(position)
        if mode == StringMode.Readable:
            return self._render_readable(digits)
        if mode == StringMode.TUI:
            return self._render_tui(digits)
        raise NotImplementedError(f"to_string() mode {mode!r} not implemented.")

    def from_string(self, strposition: str) -> int:
        raise NotImplementedError("from_string() not implemented yet.")

    def move_to_string(self, move: int, mode: StringMode) -> str:
        m=0
        for i in range(len(self.board)):
            if(self.board[i][0]==0):
                if(m==move):
                    return str(i)
                m+=1
        #return str(move)

    # -- Position packing -------------------------------------------------
    # 2 bits per mutable vertex, digit 0 in the least-significant bits.

    def _pack(self, digits: list[int]) -> int:
        position = 0
        for digit in reversed(digits):
            position = (position << 2) | digit
        return position

    def _unpack(self, position: int) -> list[int]:
        digits = [self._UNCOLORED] * self._n_digits
        for i in range(self._n_digits):
            digits[i] = position & 0b11
            position >>= 2
        return digits

    def _turn_code(self, digits: list[int]) -> int:
        colored_count = sum(1 for d in digits if d != self._UNCOLORED)
        return self._BLUE if colored_count % 2 == 0 else self._RED

    def _effective_colors(self, digits: list[int]) -> list[int]:
        """
        Returns the color of every board vertex (seeded + mutable) given
        the current digit array.
        """
        colors = [self._UNCOLORED] * len(self.board)
        for i, (seed_color, _) in enumerate(self.board):
            if seed_color != self._UNCOLORED:
                colors[i] = seed_color
            else:
                colors[i] = digits[self._board_index_to_digit[i]]
        return colors

    # -- Rendering ----------------------------------------------------------
    # Both string modes share the same hex/diamond board layout (originally
    # written for `StringMode.Readable`) -- they only differ in what label
    # each cell shows and how wide that label is.

    def _render_grid(self, cell_labels: list[str], cell_width: int) -> str:
        # The connector ("--") and diamond-footer segments keep their
        # original fixed widths regardless of label width (cell_width=1
        # reproduces the original Readable layout exactly); only the label
        # column itself widens for modes with longer labels (e.g. TUI's
        # 2-digit vertex numbers).
        conn_width = 2
        ans = ""
        for r in range(self.b_length):
            if r % 2 == 0:
                ans += " "
            for c in range(self.b_width):
                idx = r * self.b_width + c
                ans += cell_labels[idx].rjust(cell_width)
                if c < self.b_width - 1:
                    connected = (idx + 1) in self.board[idx][1]
                    ans += ("-" * conn_width) if connected else (" " * conn_width)
            ans += "\n"
            for c in range(self.b_width):
                idx = r * self.b_width + c
                if r % 2:
                    lf = (r + 1) * self.b_width + c - 1 in self.board[idx][1]
                    rf = (r + 1) * self.b_width + c in self.board[idx][1]
                    if lf and rf:
                        seg = "/\\ "
                    elif lf:
                        seg = "/  "
                    elif rf:
                        seg = " \\ " if c else "\\ "
                    else:
                        seg = "   " if c else "  "
                else:
                    lf = (r + 1) * self.b_width + c in self.board[idx][1]
                    rf = (r + 1) * self.b_width + c + 1 in self.board[idx][1]
                    if lf and rf:
                        seg = "/ \\"
                    elif lf:
                        seg = "/  "
                    elif rf:
                        seg = "  \\"
                    else:
                        seg = "   "
                # The original layout's segments are only sized correctly
                # for a 1-char label column; widen the indent (not the
                # segment itself, which has meaningful shorter/longer
                # variants of its own) to keep wider labels' footers
                # roughly aligned.
                ans += (" " * (cell_width - 1)) + seg
            ans += "\n"
        return ans

    def _render_readable(self, digits: list[int]) -> str:
        labels = []
        numz = 0
        for held, _ in self.board:
            if held == self._UNCOLORED:
                labels.append(str(digits[numz]))
                numz += 1
            else:
                labels.append(str(held))
        return self._render_grid(labels, cell_width=1)

    def _render_tui(self, digits: list[int]) -> str:
        effective = self._effective_colors(digits)
        labels = []
        for idx, color in enumerate(effective):
            if color == self._UNCOLORED:
                labels.append(str(idx))
            elif color == self._BLUE:
                labels.append("B")
            else:
                labels.append("R")
        return self._render_grid(labels, cell_width=2)

    # -- Random board generation (used only by the "board2" variant) --------

    @staticmethod
    def _variant_seed(variant_id: str) -> int:
        # Deterministic (not relying on Python's randomized hash()) so the
        # generated board is identical across processes/runs.
        seed = 0
        for ch in variant_id:
            seed = (seed * 131 + ord(ch)) & 0xFFFFFFFF
        return seed

    @staticmethod
    def _base_neighbor_coords(col: int, row: int, width: int, height: int) -> list[tuple[int, int]]:
        neighbors = []
        if col > 0:
            neighbors.append((col - 1, row))
        if col < width - 1:
            neighbors.append((col + 1, row))
        shifted_right = (row % 2 == 0)
        if row > 0:
            neighbors.append((col, row - 1))
            if shifted_right:
                if col < width - 1:
                    neighbors.append((col + 1, row - 1))
            else:
                if col > 0:
                    neighbors.append((col - 1, row - 1))
        if row < height - 1:
            neighbors.append((col, row + 1))
            if shifted_right:
                if col < width - 1:
                    neighbors.append((col + 1, row + 1))
            else:
                if col > 0:
                    neighbors.append((col - 1, row + 1))
        return neighbors

    @classmethod
    def _build_base_adjacency(cls, width: int, height: int) -> dict:
        vertices = [(col, row) for row in range(height) for col in range(width)]
        adjacency = {v: set() for v in vertices}
        # Union both directions' proposals so the result is always
        # symmetric, matching the reference's edge-set construction.
        for (col, row) in vertices:
            for neighbor in cls._base_neighbor_coords(col, row, width, height):
                adjacency[(col, row)].add(neighbor)
                adjacency[neighbor].add((col, row))
        return adjacency

    @staticmethod
    def _is_connected(vertices: set, adjacency: dict) -> bool:
        if not vertices:
            return True
        start = next(iter(vertices))
        seen = {start}
        queue = [start]
        while queue:
            current = queue.pop()
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return len(seen) == len(vertices)

    @classmethod
    def _carve_fjords(cls, vertices: set, adjacency: dict, width: int, height: int, rng: random.Random) -> None:
        for _ in range(width * height):
            vertex = (rng.randrange(width), rng.randrange(height))
            if vertex not in vertices:
                continue
            neighbors = list(adjacency[vertex])
            if not neighbors:
                continue
            neighbor = rng.choice(neighbors)
            adjacency[vertex].discard(neighbor)
            adjacency[neighbor].discard(vertex)
            if not cls._is_connected(vertices, adjacency):
                # Reverting keeps every vertex at degree >= 1, so the
                # "isolated vertex" case from the reference implementation
                # can never actually occur here.
                adjacency[vertex].add(neighbor)
                adjacency[neighbor].add(vertex)

    @classmethod
    def _place_seeds(cls, vertices: set, width: int, height: int, rng: random.Random) -> dict:
        colors = {v: cls._UNCOLORED for v in vertices}

        center_col = (width - 1) / 2
        center_row = (height - 1) / 2
        if center_row % 2 == 0:
            center_col += 0.5
        elif center_row % 1 == 0.5:
            center_col += 0.25

        def hex_distance(col: float, row: float) -> float:
            col_shifted = col + (0.5 if row % 2 == 0 else 0)
            row_dist = abs(row - center_row)
            col_dist = abs(col_shifted - center_col)
            return row_dist + max(0.0, col_dist - row_dist / 2)

        threshold = (width + height) / 3
        placed = 0
        while placed < threshold:
            blue_vertex = None
            red_vertex = None
            while True:
                blue_col, blue_row = rng.randrange(width), rng.randrange(height)
                blue_candidate = (blue_col, blue_row)
                if blue_candidate not in vertices or colors[blue_candidate] != cls._UNCOLORED:
                    continue
                blue_distance = hex_distance(blue_col, blue_row)

                red_row = rng.randrange(height)
                candidate_cols = [
                    col for col in range(width)
                    if abs(hex_distance(col, red_row) - blue_distance) < 1e-9
                ]
                rng.shuffle(candidate_cols)

                found = False
                for col in candidate_cols:
                    candidate = (col, red_row)
                    if (candidate in vertices and colors[candidate] == cls._UNCOLORED
                            and candidate != blue_candidate):
                        red_vertex = candidate
                        found = True
                        break

                if found:
                    blue_vertex = blue_candidate
                    break

            colors[blue_vertex] = cls._BLUE
            colors[red_vertex] = cls._RED
            placed += 1

        return colors

    @classmethod
    def _generate_random_board(cls, width: int, height: int, variant_id: str) -> list:
        rng = random.Random(cls._variant_seed(variant_id))
        adjacency_by_coord = cls._build_base_adjacency(width, height)
        vertices = set(adjacency_by_coord.keys())
        cls._carve_fjords(vertices, adjacency_by_coord, width, height, rng)
        colors_by_coord = cls._place_seeds(vertices, width, height, rng)

        def index(col: int, row: int) -> int:
            return row * width + col

        board = []
        for row in range(height):
            for col in range(width):
                color = colors_by_coord[(col, row)]
                neighbors = sorted(index(nc, nr) for (nc, nr) in adjacency_by_coord[(col, row)])
                board.append([color, neighbors])
        return board
