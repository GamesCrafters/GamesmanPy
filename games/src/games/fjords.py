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

    All boards are 25 vertices (5x5, row-major). "regular" is the
    assignment's reference board and "board2" is a second hand-transcribed
    layout. "random1".."random50" are generated with the edge-carving and
    seed-placement algorithm from the kyleburke.info JS reference, each from
    a fixed seed so the same variant is always the same board.
    """

    id = 'fjords'
    n_random_variants = 50
    variants = ["regular", "board2"] + [f"random{i}" for i in range(1, n_random_variants + 1)]
    n_players = 2
    cyclic = False

    _UNCOLORED = 0b00
    _BLUE = 0b01
    _RED = 0b10

    _COLOR_TO_CHAR = {_UNCOLORED: "-", _BLUE: "B", _RED: "R"}
    _CHAR_TO_COLOR = {char: color for color, char in _COLOR_TO_CHAR.items()}

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

        if variant_id == "regular":
            self.board = [[color, list(neighbors)] for color, neighbors in self._REGULAR_BOARD]
        elif variant_id == "board2":
            self.board = [[color, list(neighbors)] for color, neighbors in self._BOARD_2]
        else:
            self.board = self._random_board(variant_id)
        self._mutable_indices = [
            i for i, (color, _) in enumerate(self.board) if color == self._UNCOLORED
        ]
        self._board_index_to_digit = {
            board_index: digit for digit, board_index in enumerate(self._mutable_indices)
        }
        self._n_digits = len(self._mutable_indices)
        # Random boards draw their edges from the AUTOGUI string (one theme
        # serves every board), so remember which grid edges this board kept.
        self._draws_edges = variant_id.startswith("random")
        if self._draws_edges:
            self._edge_slots = self._grid_edge_slots()
            self._kept_edges = {
                (i, j) for i, (_, neighbors) in enumerate(self.board) for j in neighbors if i < j
            }

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

        One char per board vertex (row-major): B Blue, R Red, - uncolored.
        AUTOGUI prefixes the player to move: "1_" Blue, "2_" Red. For random
        boards it also starts with one char per possible grid edge (h/r/l by
        direction, - if carved away) and marks empty vertices "o", so the
        edges and empty dots are drawn from the string rather than a
        per-board background image.
        """
        digits = self._unpack(position)
        board = "".join(self._COLOR_TO_CHAR[c] for c in self._effective_colors(digits))
        if mode == StringMode.AUTOGUI:
            turn = "1" if self._turn_code(digits) == self._BLUE else "2"
            if self._draws_edges:
                edges = "".join(
                    direction if (i, j) in self._kept_edges else "-"
                    for i, j, direction in self._edge_slots
                )
                return f"{turn}_{edges}{board.replace('-', 'o')}"
            return f"{turn}_{board}"
        return board

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        if len(strposition) != len(self.board):
            raise ValueError(f"Expected {len(self.board)} characters, got {len(strposition)}")
        colors = []
        for char in strposition:
            if char not in self._CHAR_TO_COLOR:
                raise ValueError(f"Invalid character {char!r} in position")
            colors.append(self._CHAR_TO_COLOR[char])
        for i, (seed_color, _) in enumerate(self.board):
            if seed_color != self._UNCOLORED and colors[i] != seed_color:
                raise ValueError(f"Vertex {i} must be the fixed seed color")
        return self._pack([colors[i] for i in self._mutable_indices])

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.

        Moves are named by the real board vertex they color, not the digit index.
        """
        vertex = self._mutable_indices[move]
        if mode == StringMode.AUTOGUI:
            # On random boards the vertex centers come after the edge centers.
            center = vertex + len(self._edge_slots) if self._draws_edges else vertex
            return f"A_-_{center}_x"
        return str(vertex)

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

    # -- Random boards (the "randomN" variants) -----------------------------

    # The server builds a new Fjords object on every request, so generated
    # boards are cached per variant instead of regenerated each time.
    _RANDOM_BOARDS: dict = {}

    @classmethod
    def _random_board(cls, variant_id: str) -> list:
        if variant_id not in cls._RANDOM_BOARDS:
            # Retry with the next deterministic seed until neither player is
            # stuck from the very first move.
            attempt = 0
            while True:
                board = cls._generate_random_board(5, 5, f"{variant_id}#{attempt}")
                if cls._both_players_can_move(board):
                    break
                attempt += 1
            cls._RANDOM_BOARDS[variant_id] = board
        return [[color, list(neighbors)] for color, neighbors in cls._RANDOM_BOARDS[variant_id]]

    @classmethod
    def _both_players_can_move(cls, board: list) -> bool:
        for player in (cls._BLUE, cls._RED):
            if not any(
                color == player and any(board[n][0] == cls._UNCOLORED for n in neighbors)
                for color, neighbors in board
            ):
                return False
        return True

    @classmethod
    def _grid_edge_slots(cls) -> list[tuple[int, int, str]]:
        # Every edge of the full 5x5 grid as sorted (i, j, direction), i < j.
        # The UWAPI Fjords theme lists its edge centers in this same order.
        slots = []
        for (col, row), neighbors in cls._build_base_adjacency(5, 5).items():
            i = row * 5 + col
            for ncol, nrow in neighbors:
                j = nrow * 5 + ncol
                if i >= j:
                    continue
                if nrow == row:
                    direction = "h"
                else:
                    x_i = col + (0.5 if row % 2 == 0 else 0)
                    x_j = ncol + (0.5 if nrow % 2 == 0 else 0)
                    direction = "r" if x_j > x_i else "l"
                slots.append((i, j, direction))
        return sorted(slots)

    @staticmethod
    def _variant_seed(seed_text: str) -> int:
        # Deterministic (not relying on Python's randomized hash()) so the
        # generated board is identical across processes/runs.
        seed = 0
        for ch in seed_text:
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
            neighbors = sorted(adjacency[vertex])
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
    def _generate_random_board(cls, width: int, height: int, seed_text: str) -> list:
        rng = random.Random(cls._variant_seed(seed_text))
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
