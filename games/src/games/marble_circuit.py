from models import Game, Value, StringMode
from typing import Optional
# marble_circuit
# 口 0..3 = TL, TR, BR, BL
TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT = 0, 1, 2, 3

# 四种块路径 (in, out)，不可旋转
TEAL_DIAMOND_PATHS = [(TOP_LEFT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_LEFT), (TOP_RIGHT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_RIGHT)]
ORANGE_T_PATHS = [(TOP_LEFT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_LEFT), (TOP_RIGHT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_RIGHT)]
YELLOW_T_PATHS = [(TOP_LEFT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_LEFT), (TOP_RIGHT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_RIGHT)]
MAGENTA_4WAY_PATHS = [(TOP_LEFT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_LEFT), (TOP_RIGHT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_RIGHT)]

# 2x2 demo：边 0..3 = 上/右/下/左
TOP, RIGHT, BOTTOM, LEFT = 0, 1, 2, 3
STRAIGHT_PATHS = [(0, 2), (2, 0)]
L_PATHS = [(0, 1), (1, 0)]


def rotate_side(side: int, rotation: int) -> int:
    return (side + rotation) % 4


def rotate_paths(paths: list[tuple[int, int]], rotation: int) -> list[tuple[int, int]]:
    return [(
        rotate_side(a, rotation),
        rotate_side(b, rotation),
    ) for a, b in paths]


# 金字塔 10 格：口 0..3 = TL/TR/BR/BL。topology[slot][port] = (邻居slot, 邻居口) 或 ('exit', 目标0..4)。
# 布局 0 / 1,2 / 3,4,5 / 6,7,8,9；底排无横向，BL/BR 为出口。
PYRAMID_10_TOPOLOGY_CORNERS: list[list[tuple[int, int] | tuple[str, int] | None]] = [
    [None, None, (2, TOP_LEFT), (1, TOP_RIGHT)],
    [(0, BOTTOM_LEFT), (0, BOTTOM_RIGHT), (4, TOP_LEFT), (3, TOP_RIGHT)],
    [(1, BOTTOM_RIGHT), (5, TOP_LEFT), (5, TOP_LEFT), (4, TOP_RIGHT)],
    [(1, BOTTOM_LEFT), (1, BOTTOM_RIGHT), (7, TOP_LEFT), (6, TOP_RIGHT)],
    [(1, BOTTOM_RIGHT), (2, BOTTOM_LEFT), (8, TOP_LEFT), (7, TOP_RIGHT)],
    [(2, BOTTOM_RIGHT), (2, BOTTOM_LEFT), (9, TOP_LEFT), (8, TOP_RIGHT)],
    [(3, BOTTOM_LEFT), (3, BOTTOM_LEFT), ("exit", 1), ("exit", 0)],
    [(3, BOTTOM_RIGHT), (4, BOTTOM_LEFT), ("exit", 2), ("exit", 1)],
    [(4, BOTTOM_RIGHT), (5, BOTTOM_LEFT), ("exit", 3), ("exit", 2)],
    [(5, BOTTOM_RIGHT), None, ("exit", 4), ("exit", 3)],
]
ENTRY_START_PYRAMID = [(6, TOP_LEFT), (3, TOP_LEFT), (1, TOP_LEFT), (0, TOP_LEFT), (0, TOP_RIGHT), (2, TOP_RIGHT), (5, TOP_RIGHT), (9, TOP_RIGHT)]

# 块类型 1=T 2=O 3=Y 4=M。fixed_slots 不可 remove。
PYRAMID_CHALLENGES: dict[str, dict] = {
    "ch23": {
        "fixed_slots": (0, 1, 4, 7, 9),
        "init_board": [3, 1, 0, 0, 4, 0, 0, 2, 0, 3],
        "init_rem": (2, 1, 0, 2),
        "exit_counts": [0, 1, 4, 3, 0],
        "solution_board": [3, 1, 1, 2, 4, 4, 4, 2, 1, 3],
    },
    "ch46": {
        "fixed_slots": (3, 4, 5),
        "init_board": [0, 0, 0, 1, 4, 4, 0, 0, 0, 0],
        "init_rem": (2, 2, 2, 1),
        "exit_counts": [1, 2, 2, 2, 1],
        "solution_board": [2, 2, 4, 1, 4, 4, 1, 3, 3, 1],
    },
}

PYRAMID_10_TOPOLOGY: list[list[tuple[int, int] | tuple[str, int] | None]] = [
    [("entry", 0), (2, TOP), (1, TOP), None],
    [(0, BOTTOM), (2, LEFT), (3, TOP), None],
    [(0, RIGHT), (5, TOP), (4, TOP), (1, RIGHT)],
    [(1, BOTTOM), (4, LEFT), (6, TOP), None],
    [(2, BOTTOM), (5, LEFT), (7, TOP), (3, RIGHT)],
    [(2, RIGHT), (9, TOP), (8, TOP), (4, RIGHT)],
    [(3, BOTTOM), (7, LEFT), ("exit", 0), None],
    [(4, BOTTOM), (8, LEFT), ("exit", 1), (6, RIGHT)],
    [(5, BOTTOM), (9, LEFT), ("exit", 2), (7, RIGHT)],
    [(5, RIGHT), ("exit", 4), ("exit", 3), (8, RIGHT)],
]


class MarbleCircuit(Game):
    """Marble Circuit：10 槽金字塔、4 种块不可旋转、按出口计数判胜（ch23/ch46/…）。"""
    id = "marble_circuit"
    variants = ["ch23", "ch46"]
    n_players = 1
    cyclic = True

    NUM_SLOTS = 4
    BOARD_TOPOLOGY_2X2: list[list[tuple[int, int] | tuple[str, int] | None]] = [
        [("entry", 0), (1, LEFT), (2, TOP), None],
        [("entry", 1), None, (3, TOP), (0, RIGHT)],
        [(0, BOTTOM), (3, LEFT), ("exit", 0), None],
        [(1, BOTTOM), None, ("exit", 1), (2, RIGHT)],
    ]
    GOALS_CH1 = [(0, 0), (1, 1)]
    INIT_REM_CH1 = (1, 0)
    PYRAMID_CONFIRM_MOVE = 50
    PYRAMID_EMPTY = "□"

    def __init__(self, variant_id: str):
        if variant_id not in MarbleCircuit.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._is_pyramid = variant_id in PYRAMID_CHALLENGES
        self._ch_config = PYRAMID_CHALLENGES.get(variant_id)
        if self._is_pyramid:
            self.NUM_SLOTS = 10
            self.BOARD_TOPOLOGY = PYRAMID_10_TOPOLOGY_CORNERS
            self._board_max = 5 ** 10
            self._rem_max = 4 * 4 * 4 * 4 * 2
        else:
            self.NUM_SLOTS = 4
            self.BOARD_TOPOLOGY = MarbleCircuit.BOARD_TOPOLOGY_2X2
            self._goals = MarbleCircuit.GOALS_CH1
            self._init_rem = MarbleCircuit.INIT_REM_CH1
            self._base = 7
            self._board_max = self._base ** self.NUM_SLOTS

    def _decode(self, position: int):
        if self._is_pyramid:
            return self._decode_ch23(position)
        board_enc = position % self._board_max
        rem_enc = position // self._board_max
        rem_s = rem_enc % 2
        rem_L = rem_enc // 2
        board = []
        x = board_enc
        for _ in range(self.NUM_SLOTS):
            board.append(x % self._base)
            x //= self._base
        return board, rem_s, rem_L

    def _decode_ch23(self, position: int) -> tuple[list[int], tuple[int, int, int, int], bool]:
        board_enc = position % self._board_max
        rem_enc = position // self._board_max
        board = []
        x = board_enc
        for _ in range(10):
            board.append(x % 5)
            x //= 5
        confirmed = rem_enc >= 256
        if confirmed:
            rem_enc -= 256
        teal = rem_enc % 4
        orange = (rem_enc // 4) % 4
        yellow = (rem_enc // 16) % 4
        magenta = (rem_enc // 64) % 4
        return board, (teal, orange, yellow, magenta), confirmed

    def _encode(self, board, rem_s, rem_L=None) -> int:
        if self._is_pyramid:
            return self._encode_ch23(board, rem_s)
        rem_enc = rem_s + 2 * (rem_L or 0)
        board_enc = 0
        for i in range(self.NUM_SLOTS - 1, -1, -1):
            board_enc = board_enc * self._base + board[i]
        return board_enc + self._board_max * rem_enc

    def _encode_ch23(self, board: list[int], rem: tuple[int, int, int, int], confirmed: bool = False) -> int:
        board_enc = sum(board[i] * (5 ** i) for i in range(10))
        teal, orange, yellow, magenta = rem
        rem_enc = teal + 4 * orange + 16 * yellow + 64 * magenta
        if confirmed:
            rem_enc += 256
        return board_enc + self._board_max * rem_enc

    def _get_block_paths(self, cell: int) -> list[tuple[int, int]]:
        if self._is_pyramid:
            return self._get_block_paths_10(cell)
        if cell == 0:
            return []
        if cell in (1, 2):
            return rotate_paths(STRAIGHT_PATHS, cell - 1)
        return rotate_paths(L_PATHS, cell - 3)

    def _get_block_paths_10(self, cell: int) -> list[tuple[int, int]]:
        if cell == 0:
            return []
        if cell == 1:
            return TEAL_DIAMOND_PATHS
        if cell == 2:
            return ORANGE_T_PATHS
        if cell == 3:
            return YELLOW_T_PATHS
        if cell == 4:
            return MAGENTA_4WAY_PATHS
        return []

    def _get_topology_ch23(self, board: list[int]) -> list[list[tuple[int, int] | tuple[str, int] | None]]:
        """返回金字塔几何拓扑，当前实现与 board 无关。"""
        return PYRAMID_10_TOPOLOGY_CORNERS

    def _simulate_marble(self, board: list[int], start_entry: int) -> Optional[int]:
        if self._is_pyramid:
            slot, side = ENTRY_START_PYRAMID[start_entry]
            topo = self._get_topology_ch23(board)
        else:
            slot, side = (0, TOP) if start_entry == 0 else (1, TOP)
            topo = self.BOARD_TOPOLOGY
        visited = set()
        while True:
            if (slot, side) in visited:
                return None
            visited.add((slot, side))
            cell = board[slot]
            paths = self._get_block_paths(cell)
            out_side = None
            for a, b in paths:
                if a == side:
                    out_side = b
                    break
            if out_side is None:
                return None
            conn = topo[slot][out_side]
            if conn is None:
                return None
            if isinstance(conn[0], str):
                if conn[0] == "exit":
                    return conn[1]
                return None
            slot, side = conn

    def _simulate_marble_with_path(self, board: list[int], start_entry: int) -> tuple[Optional[int], list[tuple[int, int]]]:
        """返回 (出口id或None, 路径 [(slot, port), ...])。"""
        if not self._is_pyramid:
            ex = self._simulate_marble(board, start_entry)
            return (ex, [(0, 0)] if ex is not None else [])
        slot, side = ENTRY_START_PYRAMID[start_entry]
        topo = self._get_topology_ch23(board)
        path: list[tuple[int, int]] = [(slot, side)]
        visited = set()
        while True:
            if (slot, side) in visited:
                return (None, path)
            visited.add((slot, side))
            cell = board[slot]
            paths = self._get_block_paths(cell)
            out_side = None
            for a, b in paths:
                if a == side:
                    out_side = b
                    break
            if out_side is None:
                return (None, path)
            conn = topo[slot][out_side]
            if conn is None:
                return (None, path)
            if isinstance(conn[0], str):
                if conn[0] == "exit":
                    return (conn[1], path)
                return (None, path)
            slot, side = conn
            path.append((slot, side))

    def _trace_all_balls_ch23(self, board: list[int]) -> list[tuple[int, Optional[int], list[tuple[int, int]]]]:
        """[(球号1-8, 出口或None, 路径), ...]。"""
        return [
            (i + 1, ex, path)
            for i in range(8)
            for ex, path in [self._simulate_marble_with_path(board, i)]
        ]

    def _get_exit_counts_ch23(self, board: list[int]) -> list[int]:
        """8 球模拟，返回 5 个出口计数。"""
        counts = [0] * 5
        for entry_id in range(8):
            ex = self._simulate_marble(board, entry_id)
            if ex is not None:
                counts[ex] += 1
        return counts

    def _all_goals_met(self, board: list[int]) -> bool:
        if self._is_pyramid:
            return self._get_exit_counts_ch23(board) == list(self._ch_config["exit_counts"])
        for entry_id, exit_id in self._goals:
            if self._simulate_marble(board, entry_id) != exit_id:
                return False
        return True

    def start(self) -> int:
        if self._is_pyramid:
            cfg = self._ch_config
            return self._encode_ch23(list(cfg["init_board"]), cfg["init_rem"], False)
        return self._encode([0] * self.NUM_SLOTS, self._init_rem[0], self._init_rem[1])

    PYRAMID_REMOVE_MOVE_BASE = 40  # place 0..39, remove 40+slot

    # Image autogui center indices (must match GamesCraftersUWAPI get_marblecircuit).
    AUTOGUI_CONFIRM_CENTER = 90
    AUTOGUI_REMOVE_CENTER_BASE = 91  # + slot 0..9

    def generate_moves(self, position: int) -> list[int]:
        if self._is_pyramid:
            board, (teal, orange, yellow, magenta), confirmed = self._decode_ch23(position)
            if confirmed:
                return []
            moves = []
            rem_all_zero = (teal == 0 and orange == 0 and yellow == 0 and magenta == 0)
            board_full = all(board[slot] != 0 for slot in range(10))
            for slot in range(10):
                if board[slot] == 0:
                    rem = [(1, teal), (2, orange), (3, yellow), (4, magenta)]
                    for btype, cnt in rem:
                        if cnt > 0:
                            moves.append(slot * 4 + (btype - 1))
                elif slot not in self._ch_config["fixed_slots"]:
                    moves.append(self.PYRAMID_REMOVE_MOVE_BASE + slot)
            if board_full and rem_all_zero:
                moves.append(self.PYRAMID_CONFIRM_MOVE)
            return moves
        board, rem_s, rem_L = self._decode(position)
        moves = []
        for slot in range(self.NUM_SLOTS):
            if board[slot] != 0:
                continue
            if rem_s > 0:
                for orient in (0, 1):
                    moves.append(slot * 8 + 0 * 4 + orient)
            if rem_L > 0:
                for orient in range(4):
                    moves.append(slot * 8 + 1 * 4 + orient)
        return moves

    def do_move(self, position: int, move: int) -> int:
        if self._is_pyramid:
            board, rem, confirmed = self._decode_ch23(position)
            if confirmed:
                raise ValueError("Cannot move after confirmation")
            teal, orange, yellow, magenta = rem
            if move == self.PYRAMID_CONFIRM_MOVE:
                board_full = all(cell != 0 for cell in board)
                rem_all_zero = (teal == 0 and orange == 0 and yellow == 0 and magenta == 0)
                if not board_full or not rem_all_zero:
                    raise ValueError("Can only confirm when board is full and no blocks remain")
                return self._encode_ch23(board, (teal, orange, yellow, magenta), True)
            if move >= self.PYRAMID_REMOVE_MOVE_BASE:
                slot = move - self.PYRAMID_REMOVE_MOVE_BASE
                if slot in self._ch_config["fixed_slots"]:
                    raise ValueError("Cannot remove from fixed slot")
                btype = board[slot]
                board = list(board)
                board[slot] = 0
                if btype == 1:
                    teal += 1
                elif btype == 2:
                    orange += 1
                elif btype == 3:
                    yellow += 1
                else:
                    magenta += 1
                return self._encode_ch23(board, (teal, orange, yellow, magenta), False)
            slot = move // 4
            btype = (move % 4) + 1
            board = list(board)
            board[slot] = btype
            if btype == 1:
                teal -= 1
            elif btype == 2:
                orange -= 1
            elif btype == 3:
                yellow -= 1
            else:
                magenta -= 1
            return self._encode_ch23(board, (teal, orange, yellow, magenta), False)
        slot = move // 8
        rest = move % 8
        btype = rest // 4
        orient = rest % 4
        board, rem_s, rem_L = self._decode(position)
        cell = (1 + orient) if btype == 0 else (3 + orient)
        board[slot] = cell
        if btype == 0:
            rem_s -= 1
        else:
            rem_L -= 1
        return self._encode(board, rem_s, rem_L)

    def primitive(self, position: int) -> Optional[Value]:
        if self._is_pyramid:
            board, rem, confirmed = self._decode_ch23(position)
            if (not confirmed) or any(r > 0 for r in rem):
                return None
            return Value.Win if self._all_goals_met(board) else Value.Loss
        board, rem_s, rem_L = self._decode(position)
        if rem_s > 0 or rem_L > 0:
            return None
        return Value.Win if self._all_goals_met(board) else Value.Loss

    def get_exit_counts_display(self, position: int) -> Optional[str]:
        """终局时返回出口计数与目标对比；非金字塔或未终局返回 None。"""
        if not self._is_pyramid:
            return None
        board, rem, confirmed = self._decode_ch23(position)
        if (not confirmed) or any(r > 0 for r in rem):
            return None
        counts = self._get_exit_counts_ch23(board)
        goal = list(self._ch_config["exit_counts"])
        if counts == goal:
            return f"Your exit counts: {counts}, goal: {goal}, success!"
        return f"Your exit counts: {counts}, goal: {goal}, failed."

    def _piece_char(self, cell: int) -> str:
        if cell == 1:
            return "H"
        if cell == 2:
            return "\\"
        if cell == 3:
            return "y"
        if cell == 4:
            return "x"
        return self.PYRAMID_EMPTY

    def to_string(self, position: int, mode: StringMode) -> str:
        if self._is_pyramid:
            board, rem, confirmed = self._decode_ch23(position)
            status = "CONFIRMED" if confirmed else "UNCONFIRMED"
            board_chars = [self._piece_char(cell) for cell in board]
            goal = list(self._ch_config["exit_counts"])
            exits = self._get_exit_counts_ch23(board) if confirmed else [self.PYRAMID_EMPTY] * 5
            goal_row = " ".join(f"{v:^4}" for v in goal)
            exits_row = " ".join(f"{str(v):^4}" for v in exits)
            legend = [
                "Pieces:   H         \\         y         x",
                "        || ||     \\\\//      \\\\//      \\\\//",
                "        || ||       \\\\      //        //\\\\",
            ]
            rows = [
                "          0",
                "       1     2",
                "    3     4     5",
                "  6     7     8     9",
                f"          {board_chars[0]}",
                f"       {board_chars[1]}     {board_chars[2]}",
                f"    {board_chars[3]}     {board_chars[4]}     {board_chars[5]}",
                f"  {board_chars[6]}     {board_chars[7]}     {board_chars[8]}     {board_chars[9]}",
                "",
                goal_row,
                exits_row,
                f"remaining: H{rem[0]} \\{rem[1]} y{rem[2]} x{rem[3]}",
                f"state: {status}",
            ]
            if not confirmed:
                rows.insert(0, " o  o  o  o  o  o  o  o")
            s = "\n".join(legend + [""] + rows)
            # Single-line key: UWAPI / GamesmanUni use Readable position in URLs; multiline breaks loads.
            # 14 dots: 4 rem | 5 goals (targets) | 5 exit results — order matches UWAPI centers 14–27.
            _dots = "." * 14
            board_str = "".join(str(b) for b in board) + "TOYM" + _dots
            goals = list(self._ch_config["exit_counts"])
            if confirmed:
                ex = self._get_exit_counts_ch23(board)
                cur_parts = [str(e) for e in ex]
            else:
                cur_parts = ["-"] * 5
            goal_parts = [str(g) for g in goals]
            rem_tilde = "~".join([str(r) for r in rem] + goal_parts + cur_parts)
            autogui_line = (
                "1_"
                + board_str
                + "~"
                + rem_tilde
                + "_"
                + "_".join(str(r) for r in rem)
                + f"_{1 if confirmed else 0}"
            )
            if mode == StringMode.AUTOGUI:
                return autogui_line
            if mode == StringMode.Readable:
                return autogui_line
            return s
        board, rem_s, rem_L = self._decode(position)
        lines = [f"[{board[0]}][{board[1]}]  rem: S={rem_s} L={rem_L}", f"[{board[2]}][{board[3]}]"]
        s = "\n".join(lines)
        if mode == StringMode.AUTOGUI:
            # Use standard autogui prefix (1 = player to move) so frontend renders ImageAutoGUI.
            return "1_" + "".join(str(b) for b in board) + f"_{rem_s}_{rem_L}"
        return s

    def from_string(self, strposition: str) -> int:
        s = strposition.strip()
        if len(s) >= 2 and s[1] == "_" and s[0] in "012":
            s = s[2:]
        if self._is_pyramid:
            parts = s.split("_")
            if len(parts) >= 5 and len(parts[0]) >= 10:
                head = parts[0].split("~")[0]
                board = [int(head[i]) for i in range(10)]
                rem = tuple(int(parts[i]) for i in range(1, 5))
                confirmed = (len(parts) >= 6 and parts[5] == "1")
            else:
                board = list(self._ch_config["init_board"])
                rem = self._ch_config["init_rem"]
                confirmed = False
            return self._encode_ch23(board, rem, confirmed)
        parts = s.split("_")
        if len(parts) >= 3 and len(parts[0]) >= 4:
            board = [int(c) for c in parts[0][:4]]
            rem_s, rem_L = int(parts[1]), int(parts[2])
        else:
            board = [0] * 4
            rem_s, rem_L = self._init_rem
            digits = "".join(c for c in s if c.isdigit())
            for i in range(min(4, len(digits))):
                board[i] = int(digits[i])
        return self._encode(board, rem_s, rem_L)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        if self._is_pyramid:
            if move == self.PYRAMID_CONFIRM_MOVE:
                if mode == StringMode.AUTOGUI:
                    # Default circle button (token not in charImages); ImageAutoGUI A_ parser.
                    return f"A_c_{self.AUTOGUI_CONFIRM_CENTER}"
                return "="
            if move >= self.PYRAMID_REMOVE_MOVE_BASE:
                slot = move - self.PYRAMID_REMOVE_MOVE_BASE
                if mode == StringMode.AUTOGUI:
                    return f"A_u_{self.AUTOGUI_REMOVE_CENTER_BASE + slot}"
                return f"{slot}-"
            slot = move // 4
            k = move % 4
            kind = ("H", "\\", "y", "x")[k]
            if mode == StringMode.AUTOGUI:
                # t/o/y/m = small move buttons; centers 50+4*slot+k (UWAPI). Board uses 1–4 for cells.
                token_char = ("t", "o", "y", "m")[k]
                center_idx = 50 + slot * 4 + k
                return f"A_{token_char}_{center_idx}"
            return f"{slot}{kind}"
        slot = move // 8
        rest = move % 8
        btype = rest // 4
        orient = rest % 4
        kind = "S" if btype == 0 else "L"
        if mode == StringMode.AUTOGUI:
            return f"MC_{slot}_{kind}{orient}"
        return f"({slot},{kind},{orient})"
