from models import Game, Value, StringMode
from typing import Optional

# 每块有四个口（不是四条边）：左上=0, 右上=1, 右下=2, 左下=3
TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT = 0, 1, 2, 3

# 块类型：通道是「从哪个口进、从哪个口出」。实物规则：不可旋转。
# ---------- 实物 4 种块（四个口：左上/右上/右下/左下）----------
# 青绿菱形 )( ：左上↔左下、右上↔右下
TEAL_DIAMOND_PATHS = [(TOP_LEFT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_LEFT), (TOP_RIGHT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_RIGHT)]
# 橘 T：左上、右上 都通 右下（左下堵）
ORANGE_T_PATHS = [(TOP_LEFT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_LEFT), (TOP_RIGHT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_RIGHT)]
# 黄 T：左上、右上 都通 左下（右下堵）
YELLOW_T_PATHS = [(TOP_LEFT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_LEFT), (TOP_RIGHT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_RIGHT)]
# 玫红四通：四个口互通
# 玫红：惯性只走两条对角线——左上↔右下、右上↔左下
MAGENTA_4WAY_PATHS = [(TOP_LEFT, BOTTOM_RIGHT), (BOTTOM_RIGHT, TOP_LEFT), (TOP_RIGHT, BOTTOM_LEFT), (BOTTOM_LEFT, TOP_RIGHT)]

# ---------- 2x2 小 demo 用（仍用 0,1,2,3 当「边」用，仅 demo）----------
# 直条/L 形用 0=上 1=右 2=下 3=左 的旧约定
TOP, RIGHT, BOTTOM, LEFT = 0, 1, 2, 3
STRAIGHT_PATHS = [(0, 2), (2, 0)]
L_PATHS = [(0, 1), (1, 0)]


def rotate_side(side: int, rotation: int) -> int:
    """旋转后的边：rotation 为 0,1,2,3 表示 0°,90°,180°,270°。"""
    return (side + rotation) % 4


def rotate_paths(paths: list[tuple[int, int]], rotation: int) -> list[tuple[int, int]]:
    """把路径列表按 rotation 旋转。"""
    return [(
        rotate_side(a, rotation),
        rotate_side(b, rotation),
    ) for a, b in paths]


# 10 位置金字塔拓扑（四口：0=左上 1=右上 2=右下 3=左下）。板子平的、无物理接线；
# 「连接」= 块上的路径（球从哪个口出）+ 摆放位置的几何相邻（谁的口对谁的口、或对出口）。
# 即：只有块摆放的位置，谁连谁由「金字塔几何」决定（谁与谁相邻、哪口对哪口），球路由块类型决定。
# 布局：第1排(0)、第2排(1,2)、第3排(3,4,5)、第4排(6,7,8,9)。底排无横向，仅从上方进、从 BL/BR 到 5 个目标。
# topology[位置][口] = (邻居位置, 邻居口) 或 ('exit', 目标编号)，入口由 ENTRY_START_CH23 指定。
PYRAMID_10_TOPOLOGY_CORNERS: list[list[tuple[int, int] | tuple[str, int] | None]] = [
    [None, None, (2, TOP_LEFT), (1, TOP_RIGHT)],                           # 0: 顶槽；BL→1-TR（0→1→…→8）, BR→2-TL
    [(0, BOTTOM_LEFT), (0, BOTTOM_RIGHT), (4, TOP_LEFT), (3, TOP_RIGHT)],   # 1: BR→4-TL（4、5号球 0→1→4→8，不经槽2）
    [(1, BOTTOM_RIGHT), (5, TOP_LEFT), (5, TOP_LEFT), (4, TOP_RIGHT)],      # 2: BR→5-TL, BL→4-TR（金字塔：2 下左邻 4、下右邻 5；6号球 2→4→7→目标3）
    [(1, BOTTOM_LEFT), (1, BOTTOM_RIGHT), (7, TOP_LEFT), (6, TOP_RIGHT)],   # 3: BL→6-TR（3号球 1→3→6 从6BR进目标2）, BR→7-TL
    [(1, BOTTOM_RIGHT), (2, BOTTOM_LEFT), (8, TOP_LEFT), (7, TOP_RIGHT)],   # 4: TL←1-BR, TR↔2-BL（金字塔：4 上右邻 2）, BL→7-TR, BR→8-TL
    [(2, BOTTOM_RIGHT), (2, BOTTOM_LEFT), (9, TOP_LEFT), (8, TOP_RIGHT)],   # 5: TL←2-BR, TR←2-BL, BR→9-TL, BL→8-TR（金字塔：5 下左邻 8、下右邻 9；7号球 5→8→目标4）
    # 底排：仅从上方接收、仅从 BL/BR 出口；无 6↔7↔8↔9 横向（重力向下）
    [(3, BOTTOM_LEFT), (3, BOTTOM_LEFT), ("exit", 1), ("exit", 0)],         # 6: TL 入口/←3-BL, TR←3-BL（3号球 3TR→6TR→6BR→目标2）, BR→目标2, BL→目标1
    [(3, BOTTOM_RIGHT), (4, BOTTOM_LEFT), ("exit", 2), ("exit", 1)],        # 7: TL←3-BR, TR←4-BL（金字塔：7 上右邻 4）, BR→目标3, BL→目标2
    [(4, BOTTOM_RIGHT), (5, BOTTOM_LEFT), ("exit", 3), ("exit", 2)],       # 8: TL←4-BR, TR←5-BL（7号球由此从8右下进目标4）, BR→目标4, BL→目标3
    [(5, BOTTOM_RIGHT), None, ("exit", 4), ("exit", 3)],                    # 9: TL←5-BR, TR 为入口, BR→目标5, BL→目标4
]
# 8 个小球入口：槽6左上、槽3左上、槽1左上、槽0左上、槽0右上、槽2右上、槽5右上、槽9右上
ENTRY_START_CH23 = [(6, TOP_LEFT), (3, TOP_LEFT), (1, TOP_LEFT), (0, TOP_LEFT), (0, TOP_RIGHT), (2, TOP_RIGHT), (5, TOP_RIGHT), (9, TOP_RIGHT)]

# 2x2 demo 仍用「边」拓扑（上/右/下/左）
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
    """
    支持 2x2_ch1（4 槽可旋转）与 ch23（10 槽金字塔、4 种块不可旋转、按出口个数判胜）。
    """
    id = "marble_circuit"
    variants = ["2x2_ch1", "ch23"]
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

    # ch23：固定块在槽 0,1,4,7,9（玩家不能 remove）；槽 2,3,5,6,8 由用户摆放、可 remove。
    # 拓扑随块摆放由 _get_topology_ch23(board) 计算，球路据此 + 块类型。
    # 块类型 1=青绿 2=橘 3=黄 4=玫红。固定：0=黄,1=青绿,4=玫红,7=橘,9=黄。
    # Solver：支持「放置」与「移除」两种操作；remoteness = 到终局的最少步数（每步放或拿都算 1 步）。
    INIT_BOARD_CH23 = [3, 1, 0, 0, 4, 0, 0, 2, 0, 3]  # 0-based；0,1,4,7,9 已摆，2,3,5,6,8 空待填
    FIXED_SLOTS_CH23 = (0, 1, 4, 7, 9)  # 固定块位置，玩家不能 remove
    INIT_REM_CH23 = (2, 1, 0, 2)  # 青绿、橘、黄、玫红 剩余
    EXIT_COUNTS_CH23 = [0, 1, 4, 3, 0]  # 5 个出口各要几颗球
    # 答案（1～10 号槽）：黄绿绿橘玫红玫红玫红橘绿黄 → 全填满后的板子
    SOLUTION_BOARD_CH23 = [3, 1, 1, 2, 4, 4, 4, 2, 1, 3]  # 0-based: 黄青绿青绿橘玫红玫红玫红橘青绿黄

    def __init__(self, variant_id: str):
        if variant_id not in MarbleCircuit.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._is_ch23 = variant_id == "ch23"
        if self._is_ch23:
            self.NUM_SLOTS = 10
            self.BOARD_TOPOLOGY = PYRAMID_10_TOPOLOGY_CORNERS  # 四个口（角）拓扑
            self._board_max = 5 ** 10
            self._rem_max = 4 * 4 * 4 * 4  # 4 种块各 0..3
        else:
            self.NUM_SLOTS = 4
            self.BOARD_TOPOLOGY = MarbleCircuit.BOARD_TOPOLOGY_2X2
            self._goals = MarbleCircuit.GOALS_CH1
            self._init_rem = MarbleCircuit.INIT_REM_CH1
            self._base = 7
            self._board_max = self._base ** self.NUM_SLOTS

    def _decode(self, position: int):
        if self._is_ch23:
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

    def _decode_ch23(self, position: int) -> tuple[list[int], tuple[int, int, int, int]]:
        board_enc = position % self._board_max
        rem_enc = position // self._board_max
        board = []
        x = board_enc
        for _ in range(10):
            board.append(x % 5)
            x //= 5
        teal = rem_enc % 4
        orange = (rem_enc // 4) % 4
        yellow = (rem_enc // 16) % 4
        magenta = (rem_enc // 64) % 4
        return board, (teal, orange, yellow, magenta)

    def _encode(self, board, rem_s, rem_L=None) -> int:
        if self._is_ch23:
            return self._encode_ch23(board, rem_s)
        rem_enc = rem_s + 2 * (rem_L or 0)
        board_enc = 0
        for i in range(self.NUM_SLOTS - 1, -1, -1):
            board_enc = board_enc * self._base + board[i]
        return board_enc + self._board_max * rem_enc

    def _encode_ch23(self, board: list[int], rem: tuple[int, int, int, int]) -> int:
        board_enc = sum(board[i] * (5 ** i) for i in range(10))
        teal, orange, yellow, magenta = rem
        rem_enc = teal + 4 * orange + 16 * yellow + 64 * magenta
        return board_enc + self._board_max * rem_enc

    def _get_block_paths(self, cell: int) -> list[tuple[int, int]]:
        if self._is_ch23:
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
        """ch23：返回当前局对应的拓扑。板子无接线，连接 = 块上路径 + 位置几何相邻。
        谁的口连到谁的口（或出口）由金字塔摆放几何唯一确定；球从哪口进、从哪口出由各位置上的块类型决定。
        此处返回几何拓扑表（与摆放位置对应），不随 board 内容改变；若以后需「空位时连接不同」等规则可在此扩展。"""
        return PYRAMID_10_TOPOLOGY_CORNERS

    def _simulate_marble(self, board: list[int], start_entry: int) -> Optional[int]:
        if self._is_ch23:
            slot, side = ENTRY_START_CH23[start_entry]
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
                return None  # 不应从块走回 entry
            slot, side = conn

    def _simulate_marble_with_path(self, board: list[int], start_entry: int) -> tuple[Optional[int], list[tuple[int, int]]]:
        """ch23：模拟一颗球，返回 (出口id或None, 路径 [(slot, port), ...])。"""
        if not self._is_ch23:
            ex = self._simulate_marble(board, start_entry)
            return (ex, [(0, 0)] if ex is not None else [])
        slot, side = ENTRY_START_CH23[start_entry]
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
        """ch23：返回 [(球号1-8, 出口id或None, 路径), ...]。"""
        return [
            (i + 1, ex, path)
            for i in range(8)
            for ex, path in [self._simulate_marble_with_path(board, i)]
        ]

    def _get_exit_counts_ch23(self, board: list[int]) -> list[int]:
        """ch23：模拟 8 颗球，返回 5 个出口各自进球数。"""
        counts = [0] * 5
        for entry_id in range(8):
            ex = self._simulate_marble(board, entry_id)
            if ex is not None:
                counts[ex] += 1
        return counts

    def _all_goals_met(self, board: list[int]) -> bool:
        if self._is_ch23:
            return self._get_exit_counts_ch23(board) == list(MarbleCircuit.EXIT_COUNTS_CH23)
        for entry_id, exit_id in self._goals:
            if self._simulate_marble(board, entry_id) != exit_id:
                return False
        return True

    def start(self) -> int:
        if self._is_ch23:
            return self._encode_ch23(list(MarbleCircuit.INIT_BOARD_CH23), MarbleCircuit.INIT_REM_CH23)
        return self._encode([0] * self.NUM_SLOTS, self._init_rem[0], self._init_rem[1])

    # ch23：放置 move 0..39 = slot*4+(btype-1)；移除 move 40..49 = 40+slot
    CH23_REMOVE_MOVE_BASE = 40

    def generate_moves(self, position: int) -> list[int]:
        if self._is_ch23:
            board, (teal, orange, yellow, magenta) = self._decode_ch23(position)
            moves = []
            rem_all_zero = (teal == 0 and orange == 0 and yellow == 0 and magenta == 0)
            board_full = all(board[slot] != 0 for slot in range(10))
            if board_full and rem_all_zero:
                return []  # 终局：不再允许 remove，由 primitive 判胜负
            for slot in range(10):
                if board[slot] == 0:
                    rem = [(1, teal), (2, orange), (3, yellow), (4, magenta)]
                    for btype, cnt in rem:
                        if cnt > 0:
                            moves.append(slot * 4 + (btype - 1))  # place
                elif slot not in MarbleCircuit.FIXED_SLOTS_CH23:
                    moves.append(self.CH23_REMOVE_MOVE_BASE + slot)  # remove（仅非固定槽）
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
        if self._is_ch23:
            board, rem = self._decode_ch23(position)
            teal, orange, yellow, magenta = rem
            if move >= self.CH23_REMOVE_MOVE_BASE:
                slot = move - self.CH23_REMOVE_MOVE_BASE
                if slot in MarbleCircuit.FIXED_SLOTS_CH23:
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
                return self._encode_ch23(board, (teal, orange, yellow, magenta))
            slot = move // 4
            btype = (move % 4) + 1  # 1..4
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
            return self._encode_ch23(board, (teal, orange, yellow, magenta))
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
        if self._is_ch23:
            board, rem = self._decode_ch23(position)
            if any(r > 0 for r in rem):
                return None
            return Value.Win if self._all_goals_met(board) else Value.Loss

    def get_exit_counts_display(self, position: int) -> Optional[str]:
        """ch23: at game end return a line with your exit counts, goal, and success/fail. None if not ch23 or not terminal."""
        if not self._is_ch23:
            return None
        board, rem = self._decode_ch23(position)
        if any(r > 0 for r in rem):
            return None
        counts = self._get_exit_counts_ch23(board)
        goal = list(MarbleCircuit.EXIT_COUNTS_CH23)
        if counts == goal:
            return f"Your exit counts: {counts}, goal: {goal}, success!"
        # 失败时打印每颗球的路径，便于核对
        port_name = ("TL", "TR", "BR", "BL")
        lines = [f"Your exit counts: {counts}, goal: {goal}, failed."]
        for ball_id, ex, path in self._trace_all_balls_ch23(board):
            path_s = "→".join(f"{s}{port_name[p]}" for s, p in path)
            ex_s = f"目标{ex+1}" if ex is not None else "未出口"
            lines.append(f"  {ball_id}号球: {path_s} → {ex_s}")
        return "\n".join(lines)

    def to_string(self, position: int, mode: StringMode) -> str:
        if self._is_ch23:
            board, rem = self._decode_ch23(position)
            s = " ".join(str(b) for b in board) + " | T%d O%d Y%d M%d" % rem
            if mode == StringMode.AUTOGUI:
                return "0_" + "".join(str(b) for b in board) + "_" + "_".join(str(r) for r in rem)
            return s
        board, rem_s, rem_L = self._decode(position)
        lines = [f"[{board[0]}][{board[1]}]  rem: S={rem_s} L={rem_L}", f"[{board[2]}][{board[3]}]"]
        s = "\n".join(lines)
        if mode == StringMode.AUTOGUI:
            return "0_" + "".join(str(b) for b in board) + f"_{rem_s}_{rem_L}"
        return s

    def from_string(self, strposition: str) -> int:
        s = strposition.strip()
        if s.startswith("0_"):
            s = s[2:]
        if self._is_ch23:
            parts = s.split("_")
            if len(parts) >= 5 and len(parts[0]) >= 10:
                board = [int(c) for c in parts[0][:10]]
                rem = tuple(int(parts[i]) for i in range(1, 5))
            else:
                board = list(MarbleCircuit.INIT_BOARD_CH23)
                rem = MarbleCircuit.INIT_REM_CH23
            return self._encode_ch23(board, rem)
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
        if self._is_ch23:
            if move >= self.CH23_REMOVE_MOVE_BASE:
                slot = move - self.CH23_REMOVE_MOVE_BASE
                if mode == StringMode.AUTOGUI:
                    return f"R_{slot}_x"
                return f"({slot},-)"
            slot = move // 4
            k = move % 4
            kind = ("T", "O", "Y", "M")[k]
            if mode == StringMode.AUTOGUI:
                return f"M_{slot}_{kind}_x"
            return f"({slot},{kind})"
        slot = move // 8
        rest = move % 8
        btype = rest // 4
        orient = rest % 4
        kind = "S" if btype == 0 else "L"
        if mode == StringMode.AUTOGUI:
            return f"M_{slot}_{kind}{orient}_x"
        return f"({slot},{kind},{orient})"
