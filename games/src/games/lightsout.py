from models import Game, Value, StringMode
from typing import Optional

class LightsOut(Game):
    """
    Lights Out Puzzle: 在 m×n 灯阵上，每次按一格会翻转该格及上下左右共五盏灯。
    目标：从给定初始状态把所有灯关掉。
    位置用 Z_2 上的矩阵表示，一步操作对应 L + A_ij (mod 2)，即 XOR 该格及其四邻的掩码。
    """
    id = 'lightsout'
    variants = ["3x2", "3x3", "4x4", "5x5"]
    n_players = 1
    cyclic = True

    def __init__(self, variant_id: str):
        if variant_id not in LightsOut.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        parts = variant_id.split(sep="x")
        self._rows = int(parts[0])
        self._cols = int(parts[1])
        self._n = self._rows * self._cols
        # 预计算每个格子按下时的 XOR 掩码（该格+上下左右，在边界内）
        self._toggle_masks: list[int] = []
        for i in range(self._rows):
            for j in range(self._cols):
                mask = 0
                for di, dj in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < self._rows and 0 <= nj < self._cols:
                        mask |= 1 << (ni * self._cols + nj)
                self._toggle_masks.append(mask)

    def start(self) -> int:
        """起始局面：全部灯亮（全 1 矩阵）。"""
        return (1 << self._n) - 1

    def generate_moves(self, position: int) -> list[int]:
        """任意未亮的局面都可按任意格子，返回所有格子索引。若已全灭则无步可走。"""
        if position == 0:
            return []
        return list(range(self._n))

    def do_move(self, position: int, move: int) -> int:
        """在 position 上按 move 格：L + A_ij (mod 2) = position XOR toggle_mask[move]。"""
        return position ^ self._toggle_masks[move]

    def primitive(self, position: int) -> Optional[Value]:
        """全灭（零矩阵）为终局，当前玩家获胜。"""
        if position == 0:
            return Value.Win
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """位置的可读/自动界面表示：每行一串 0/1，行间换行。"""
        rows: list[str] = []
        for i in range(self._rows):
            row = ""
            for j in range(self._cols):
                k = i * self._cols + j
                row += "1" if (position >> k) & 1 else "0"
            rows.append(row)
        s = "\n".join(rows)
        if mode == StringMode.AUTOGUI:
            return "0_" + s.replace("\n", "")
        return s

    def from_string(self, strposition: str) -> int:
        """从 Readable 格式还原位置（多行 0/1 或单行 0_...）。"""
        s = strposition.strip()
        if s.startswith("0_"):
            s = s[2:]
        s = s.replace("\n", "").replace(" ", "")
        pos = 0
        for i, c in enumerate(s):
            if i >= self._n:
                break
            if c == "1":
                pos |= 1 << i
        return pos

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """一步用 (行, 列) 表示，行列从 0 起。"""
        r = move // self._cols
        c = move % self._cols
        if mode == StringMode.AUTOGUI:
            return f"M_{move}_x"
        return f"({r},{c})"
