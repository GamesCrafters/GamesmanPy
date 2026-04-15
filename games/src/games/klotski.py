from models import Game, Value, StringMode
from typing import Optional

class Klotski(Game):
    id = 'klotski'
    variants = ["donkey", "pennant"]
    n_players = 1
    cyclic = True

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Klotski.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id

        if (variant_id == "donkey"):
            self.numPieces = 10
            self.num11 = 4
            self.num12 = 1
            self.num21 = 4
            self.num22 = 1
            self.goal_anchor = 6
        elif (variant_id == "pennant"):
            self.numPieces = 9
            self.num11 = 2
            self.num12 = 4
            self.num21 = 2
            self.num22 = 1
            self.goal_anchor = 7


        self.TWO_BY_TWO = 0
        self.TWO_BY_ONE = 1
        self.ONE_BY_TWO = 2
        self.ONE_BY_ONE = 3

        self.MOVE_CODE_UP = 0
        self.MOVE_CODE_DOWN = 1
        self.MOVE_CODE_LEFT = 2
        self.MOVE_CODE_RIGHT = 3

        self.LEFT_EDGE = sum(1 << c for c in (19,15,11,7,3))
        self.RIGHT_EDGE = sum(1 << c for c in (16,12,8,4,0))
        self.TOP_EDGE = sum(1 << c for c in (19,18,17,16))
        self.BOT_EDGE = sum(1 << c for c in (3,2,1,0))
        self.BOARD_MASK = (1 << 20) - 1

        # group boundaries in decode order (LSB->MSB): 11, 12, 21, 22
        self.end11 = self.num11
        self.end12 = self.num11 + self.num12
        self.end21 = self.num11 + self.num12 + self.num21
        self.end22 = self.numPieces

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        if (self._variant_id == "donkey"):
            return 0b10010_10011_10000_01011_01000_01010_00110_00101_00011_00000
        elif (self._variant_id == "pennant"):
            return 0b10011_00111_00110_10001_01101_00101_00001_01011_01010
        
        # invalid variant
        raise ValueError("Variant not defined")
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        bitboard = 0
        moveList = []

        for i in range(self.numPieces):
            # Populate bitboard
            pieceLocation = (position >> (i*5)) & 0b11111
            pieceType = 0
            if (i < self.num11):
                # 1 by 1 piece
                bitboard |= 1 << pieceLocation
            elif (i < self.num11 + self.num12):
                # 1 by 2 piece
                bitboard |= 1 << pieceLocation
                bitboard |= 1 << (pieceLocation - 1)
            elif (i < self.num11 + self.num12 + self.num21):
                # 2 by 1 piece
                bitboard |= 1 << pieceLocation
                bitboard |= 1 << (pieceLocation - 4)
            else:
                # 2 by 2 piece
                bitboard |= 1 << pieceLocation
                bitboard |= 1 << (pieceLocation - 1)
                bitboard |= 1 << (pieceLocation - 4)
                bitboard |= 1 << (pieceLocation - 5)

        for i in range(self.numPieces):
            # Figure out the piece type and location
            pieceLocation = (position >> (i*5)) & 0b11111
            pieceMask = 0
            if (i < self.num11):
                pieceMask |= 1 << pieceLocation
            elif (i < self.num11 + self.num12):
                pieceMask |= 1 << pieceLocation
                pieceMask |= 1 << (pieceLocation - 1)
            elif (i < self.num11 + self.num12 + self.num21):
                pieceMask |= 1 << pieceLocation
                pieceMask |= 1 << (pieceLocation - 4)
            else:
                pieceMask |= 1 << pieceLocation
                pieceMask |= 1 << (pieceLocation - 1)
                pieceMask |= 1 << (pieceLocation - 4)
                pieceMask |= 1 << (pieceLocation - 5)

            # Up movement
            shiftedMask = (pieceMask << 4) & self.BOARD_MASK
            if (((bitboard & ~pieceMask) & shiftedMask) == 0):
                # Check border
                if (pieceMask & self.TOP_EDGE) == 0:
                    # Add move to list of moves
                    moveCode = (i << 2) + self.MOVE_CODE_UP
                    moveList.append(moveCode)

            # Down movement
            shiftedMask = pieceMask >> 4
            if (((bitboard & ~pieceMask) & shiftedMask) == 0):
                # Check border
                if (pieceMask & self.BOT_EDGE) == 0:
                    # Add move to list of moves
                    moveCode = (i << 2) + self.MOVE_CODE_DOWN
                    moveList.append(moveCode)

            # Left movement
            shiftedMask = (pieceMask << 1) & self.BOARD_MASK
            if (((bitboard & ~pieceMask) & shiftedMask) == 0):
                # Check border
                if (pieceMask & self.LEFT_EDGE) == 0:
                    # Add move to list of moves
                    moveCode = (i << 2) + self.MOVE_CODE_LEFT
                    moveList.append(moveCode)

            # Right movement
            shiftedMask = pieceMask >> 1
            if (((bitboard & ~pieceMask) & shiftedMask) == 0):
                # Check border
                if (pieceMask & self.RIGHT_EDGE) == 0:
                    # Add move to list of moves
                    moveCode = (i << 2) + self.MOVE_CODE_RIGHT
                    moveList.append(moveCode)

        return moveList
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """

        piece_index = move >> 2
        direction = move & 0b11

        a = self._get_anchor(position, piece_index)

        if direction == self.MOVE_CODE_UP:
            na = a + 4
        elif direction == self.MOVE_CODE_DOWN:
            na = a - 4
        elif direction == self.MOVE_CODE_LEFT:
            na = a + 1
        elif direction == self.MOVE_CODE_RIGHT:
            na = a - 1
        else:
            raise ValueError("Invalid move direction")

        newpos = self._set_anchor(position, piece_index, na)

        
        return self._canonicalize(newpos)

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        goal_index = self.end21
        if self._get_anchor(position, goal_index) == self.goal_anchor:
            return Value.Win
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        grid = [['-' for _ in range(4)] for _ in range(5)]

        def place(cells, ch):
            for cell in cells:
                row = (19 - cell) // 4
                col = (19 - cell) % 4
                grid[row][col] = ch

        labels = [chr(ord('A') + i) for i in range(self.numPieces)]

        for i in range(self.numPieces):
            a = self._get_anchor(position, i)
            if mode == StringMode.AUTOGUI:
                if i < self.end11:
                    place([a], 'o')
                elif i < self.end12:
                    place([a], 'H')
                    place([a - 1], 'h')
                elif i < self.end21:
                    place([a], 'V')
                    place([a - 4], 'v')
                else:
                    place([a], 'W')
                    place([a - 1], 'X')
                    place([a - 4], 'Y')
                    place([a - 5], 'Z')
            else:
                ch = labels[i]
                if i < self.end11:
                    cells = [a]
                elif i < self.end12:
                    cells = [a, a - 1]
                elif i < self.end21:
                    cells = [a, a - 4]
                else:
                    cells = [a, a - 1, a - 4, a - 5]
                place(cells, ch)

        flat = ''.join(grid[r][c] for r in range(5) for c in range(4))

        if mode == StringMode.AUTOGUI:
            return '1_' + flat
        elif mode == StringMode.TUI:
            lines = [' '.join(grid[r]) for r in range(5)]
            return '\n'.join(lines)
        else:
            return flat

    def from_string(self, strposition: str) -> int:
        if strposition.startswith('1_'):
            flat = strposition[2:]
        else:
            flat = strposition.strip()

        if len(flat) == 20:
            pass  # already the flat format
        else:
            raise ValueError(f"Expected 20 characters, got {len(flat)}: {repr(flat)}")

        def rc_to_cell(r, c):
            return 19 - (r * 4 + c)

        occ: dict[str, list[int]] = {}
        for r in range(5):
            for c in range(4):
                ch = flat[r * 4 + c]
                if ch == '-':
                    continue
                occ.setdefault(ch, []).append(rc_to_cell(r, c))

        anchors = []
        for i in range(self.numPieces):
            ch = chr(ord('A') + i)
            plist = occ.get(ch, [])
            plist.sort(reverse=True)
            anchors.append(plist[0])

        pos = 0
        for i, a in enumerate(anchors):
            pos |= (a & 0b11111) << (5 * i)
        return pos 

    # def move_to_string(self, move: int, mode: StringMode, position: int = 0) -> str:
    #     i = move >> 2
    #     d = move & 0b11

    #     if mode == StringMode.AUTOGUI:
    #         a = self._get_anchor(position, i)
    #         from_idx = self._center_index(i, a)

    #         if d == self.MOVE_CODE_UP:
    #             to_idx = self._center_index(i, a + 4)
    #             char = '↑'
    #         elif d == self.MOVE_CODE_DOWN:
    #             to_idx = self._center_index(i, a - 4)
    #             char = '↓'
    #         elif d == self.MOVE_CODE_LEFT:
    #             to_idx = self._center_index(i, a + 1)
    #             char = '←'
    #         else:
    #             to_idx = self._center_index(i, a - 1)
    #             char = '→'
    #         return f"M_{from_idx}_{to_idx}_{char}"

    #     iChar = chr(ord('A') + i)
    #     dChar = {self.MOVE_CODE_UP: "U", self.MOVE_CODE_DOWN: "D",
    #             self.MOVE_CODE_LEFT: "L", self.MOVE_CODE_RIGHT: "R"}[d]
    #     return f"{iChar}{dChar}"

    def move_to_string(self, move: int, mode: StringMode, position: int = 0) -> str:
        i = move >> 2
        d = move & 0b11

        if mode == StringMode.AUTOGUI:
            a = self._get_anchor(position, i)
            autogui_a = 19 - a
            row = autogui_a // 4
            col = autogui_a % 4

            char = {self.MOVE_CODE_UP: '↑', self.MOVE_CODE_DOWN: '↓',
                    self.MOVE_CODE_LEFT: '←', self.MOVE_CODE_RIGHT: '→'}[d]

            if i < self.end11:
                from_idx = autogui_a
                delta = {self.MOVE_CODE_UP: -4, self.MOVE_CODE_DOWN: 4,
                        self.MOVE_CODE_LEFT: -1, self.MOVE_CODE_RIGHT: 1}[d]
                to_idx = autogui_a + delta

            elif i < self.end12:
                if d == self.MOVE_CODE_UP:
                    from_idx = 20 + col*5 + row
                    to_idx   = 63 + col*5 + row
                elif d == self.MOVE_CODE_DOWN:
                    from_idx = 20 + col*5 + row
                    to_idx   = 78 + col*5 + row
                elif d == self.MOVE_CODE_LEFT:
                    from_idx = autogui_a
                    to_idx   = 93 + col*5 + row
                else:
                    from_idx = 108 + col*5 + row
                    to_idx   = 123 + col*5 + row

            elif i < self.end21:
                if d == self.MOVE_CODE_UP:
                    from_idx = autogui_a
                    to_idx   = 138 + col*4 + row
                elif d == self.MOVE_CODE_DOWN:
                    from_idx = autogui_a + 4
                    to_idx   = 154 + col*4 + row
                elif d == self.MOVE_CODE_LEFT:
                    from_idx = 35 + col*4 + row
                    to_idx   = 170 + col*4 + row
                else:
                    from_idx = 35 + col*4 + row
                    to_idx   = 186 + col*4 + row

            else:
                if d == self.MOVE_CODE_UP:
                    from_idx = 202 + col*4 + row
                    to_idx   = 214 + col*4 + row
                elif d == self.MOVE_CODE_DOWN:
                    from_idx = 226 + col*4 + row
                    to_idx   = 238 + col*4 + row
                elif d == self.MOVE_CODE_LEFT:
                    from_idx = 250 + col*4 + row
                    to_idx   = 262 + col*4 + row
                else:
                    from_idx = 274 + col*4 + row
                    to_idx   = 286 + col*4 + row

            return f"M_{from_idx}_{to_idx}_{char}"

        iChar = chr(ord('A') + i)
        dChar = {self.MOVE_CODE_UP: "U", self.MOVE_CODE_DOWN: "D",
                self.MOVE_CODE_LEFT: "L", self.MOVE_CODE_RIGHT: "R"}[d]
        return f"{iChar}{dChar}"
    
    # ---------- helpers ----------

    def _get_anchor(self, position: int, i: int) -> int:
        return (position >> (5 * i)) & 0b11111

    def _set_anchor(self, position: int, i: int, anchor: int) -> int:
        shift = 5 * i
        position &= ~(0b11111 << shift)
        position |= (anchor & 0b11111) << shift
        return position

    def _piece_mask(self, i: int, anchor: int) -> int:
        """
        Your convention:
          1x2 = horizontal => anchor and anchor-1
          2x1 = vertical   => anchor and anchor-4
          2x2 = anchor, anchor-1, anchor-4, anchor-5
        Anchor is top-left of the piece.
        """
        if i < self.end11:
            return 1 << anchor
        elif i < self.end12:
            return (1 << anchor) | (1 << (anchor - 1))
        elif i < self.end21:
            return (1 << anchor) | (1 << (anchor - 4))
        else:
            return (1 << anchor) | (1 << (anchor - 1)) | (1 << (anchor - 4)) | (1 << (anchor - 5))

    def _canonicalize(self, position: int) -> int:
        """
        Sort anchors within each identical-type group so permutations of identical pieces
        map to the same integer state.
        """
        anchors = [self._get_anchor(position, i) for i in range(self.numPieces)]

        # groups: [0,end11), [end11,end12), [end12,end21), [end21,end22)
        anchors[0:self.end11] = sorted(anchors[0:self.end11])
        anchors[self.end11:self.end12] = sorted(anchors[self.end11:self.end12])
        anchors[self.end12:self.end21] = sorted(anchors[self.end12:self.end21])
        anchors[self.end21:self.end22] = sorted(anchors[self.end21:self.end22])

        out = 0
        for i, a in enumerate(anchors):
            out |= (a & 0b11111) << (5 * i)
        return out

    def _occupancy_bitboard(self, position: int) -> int:
        occ = 0
        for i in range(self.numPieces):
            a = self._get_anchor(position, i)
            occ |= self._piece_mask(i, a)
        return occ
    
    def _center_index(self, i, a):
        """
        Returns the index into the imageAutoGUIData centers array
        corresponding to the visual center of piece i at anchor a.
        Board cells occupy indices 0-19.
        Extra centers:
        1x2 horizontal: indices 20-34 (col_left * 5 + row_top)
        2x1 vertical:   indices 35-50 (col * 4 + row_top)  -- wait, col*4+row_top
        2x2:            indices 51-62 (col_left * 4 + row_top)
        """
        autogui = 19 - a
        row = autogui // 4
        col = autogui % 4

        if i < self.end11:
            return autogui                    # 1x1: use cell center directly
        elif i < self.end12:
            return 20 + col * 5 + row         # 1x2 horizontal
        elif i < self.end21:
            return 35 + col * 4 + row         # 2x1 vertical
        else:
            return 51 + col * 4 + row         # 2x2