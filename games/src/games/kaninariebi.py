from models import Game, Value, StringMode
from typing import Optional

class KaniNariEbi(Game):
    id = 'kaninariebi'
    variants = ["regular", "mixed"]
    n_players = 2
    cyclic = True

    # Initialization Helper Variables:
    _ROWS = 5
    _COLS = 5
    _BOARD_SIZE = 25

    _EMPTY = 0
    _P1_CRAB = 1
    _P1_SHRIMP = 2
    _P2_CRAB = 3
    _P2_SHRIMP = 4

    _CURRENT_NONE = 0
    _CURRENT_UP = 1
    _CURRENT_DOWN = 2

    _ORTHOGONAL = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    )

    _DIAGONAL = (
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    )

    _PIECE_TO_CHAR = {
        _EMPTY: "-",
        _P1_CRAB: "C",
        _P1_SHRIMP: "S",
        _P2_CRAB: "c",
        _P2_SHRIMP: "s",
    }
    _CHAR_TO_PIECE = {v: k for k, v in _PIECE_TO_CHAR.items()}
    
    # ---------------------------- Move bit layout ----------------------------
    # One part-move uses 13 bits:
    #   bits  0..4  : src       (0..24)
    #   bits  5..9  : dest      (0..24), BEFORE sea current
    #   bits 10..11 : current   (0 none, 1 up, 2 down)
    #   bit      12 : promote   (0/1)
    #
    # Full move:
    #   bits  0..12 : main part
    #   bits 13..25 : Bond part
    #   bit      26 : whether Bond part exists
    _PART_BITS = 13
    _PART_MASK = (1 << _PART_BITS) - 1
    _BOND_FLAG_BIT = 26

    # ========================================================
    # General Board Helpers
    # ========================================================
    @staticmethod
    def _index(row: int, col: int) -> int:
        return row * 5 + col

    @staticmethod
    def _coord(index: int) -> tuple[int, int]:
        return divmod(index, 5)

    @staticmethod
    def _on_board(row: int, col: int) -> bool:
        return 0 <= row < 5 and 0 <= col < 5

    def _owner(self, piece: int) -> int:
        if piece in (self._P1_CRAB, self._P1_SHRIMP):
            return 1
        if piece in (self._P2_CRAB, self._P2_SHRIMP):
            return 2
        return 0

    def _is_crab(self, piece: int) -> bool:
        return piece in (self._P1_CRAB, self._P2_CRAB)

    def _is_shrimp(self, piece: int) -> bool:
        return piece in (self._P1_SHRIMP, self._P2_SHRIMP)

    def _crab_piece(self, player: int) -> int:
        return self._P1_CRAB if player == 1 else self._P2_CRAB

    def _shrimp_piece(self, player: int) -> int:
        return self._P1_SHRIMP if player == 1 else self._P2_SHRIMP

    @staticmethod
    def _opponent_home_col(player: int) -> int:
        # Player 1 starts on col 0 and promotes on col 4.
        # Player 2 starts on col 4 and promotes on col 0.
        return 4 if player == 1 else 0

    # ===============================================================
    # Hashing / Unhashing Board
    # ===============================================================
    def _hash_position(self, board: list[int], turn: int) -> int:
        position = 0
        multiplier = 1

        for piece in board:
            position += piece * multiplier
            multiplier *= 5

        return position * 2 + (turn - 1)


    def _unhash_position(self, position: int) -> tuple[list[int], int]:
        turn = (position % 2) + 1
        position //= 2

        board = [self._EMPTY] * self._BOARD_SIZE

        for i in range(self._BOARD_SIZE):
            board[i] = position % 5
            position //= 5

        return board, turn

    # converts a move to a String 
    # Convert binary move representation to a string move
    # ex. 0b01110101110 -> "b2-2-u-d1-3-d"
    def _part_to_string(self, part_code: int) -> str:
        src, dest, current, promote = self._unpack_part(part_code)

        # text = f"{self._square_name(src)}-{dest}-"

        # if current == self._CURRENT_UP:
        #     text += "u"
        # elif current == self._CURRENT_DOWN:
        #     text += "d"

        # if promote:
        #     text += "1"
        # else:
        #     text += "0"

        text = f"{self._square_name(src)}->{self._square_name(dest)}"

        if current == self._CURRENT_UP:
            text += " current=up"
        elif current == self._CURRENT_DOWN:
            text += " current=down"

        if promote:
            text += " promote"

        return text
    
    @staticmethod
    def _square_name(square: int) -> str:
        row, col = divmod(square, 5)
        # Top row is rank 5, bottom row rank 1.
        return f"{chr(ord('a') + col)}{5 - row}"

    # ========================================================================
    # Move encoding
    # ========================================================================

    def _pack_part(
        self,
        src: int,
        dest: int,
        current: int,
        promote: bool,
    ) -> int:
        return (
            src
            | (dest << 5)
            | (current << 10)
            | (int(promote) << 12)
        )

    def _unpack_part(self, code: int) -> tuple[int, int, int, bool]:
        src = code & 0b11111
        dest = (code >> 5) & 0b11111
        current = (code >> 10) & 0b11
        promote = bool((code >> 12) & 1)
        return src, dest, current, promote

    def _pack_move(self, main_part: int, bond_part: Optional[int] = None) -> int:
        move = main_part
        if bond_part is not None:
            move |= bond_part << self._PART_BITS
            move |= 1 << self._BOND_FLAG_BIT
        return move

    def _unpack_move(self, move: int) -> tuple[int, Optional[int]]:
        main_part = move & self._PART_MASK
        has_bond = bool((move >> self._BOND_FLAG_BIT) & 1)

        bond_part = None
        if has_bond:
            bond_part = (move >> self._PART_BITS) & self._PART_MASK

        return main_part, bond_part

    # ========================================================================
    # Normal movement
    # ========================================================================

    def _normal_destinations(self, board: list[int], src: int) -> list[int]:
        piece = board[src]
        row, col = self._coord(src)
        destinations: list[int] = []

        # Crab: any number of empty squares horizontally, no jumping.
        if self._is_crab(piece):
            for dc in (-1, 1):
                new_col = col + dc

                while 0 <= new_col < self._COLS:
                    dest = self._index(row, new_col)
                    if board[dest] != self._EMPTY:
                        break

                    destinations.append(dest)
                    new_col += dc

        # Shrimp: exactly one diagonal square.
        elif self._is_shrimp(piece):
            for dr, dc in self._DIAGONAL:
                new_row = row + dr
                new_col = col + dc

                if not self._on_board(new_row, new_col):
                    continue

                dest = self._index(new_row, new_col)
                if board[dest] == self._EMPTY:
                    destinations.append(dest)

        return destinations

    def _bond_destinations(self, board: list[int], src: int) -> list[int]:
        """Bond bonus: ANY bonded piece moves exactly one diagonal square."""
        row, col = self._coord(src)
        destinations: list[int] = []

        for dr, dc in self._DIAGONAL:
            new_row = row + dr
            new_col = col + dc

            if not self._on_board(new_row, new_col):
                continue

            dest = self._index(new_row, new_col)
            if board[dest] == self._EMPTY:
                destinations.append(dest)

        return destinations

    @staticmethod
    def _move_piece(board: list[int], src: int, dest: int) -> list[int]:
        new_board = board.copy()
        new_board[dest] = new_board[src]
        new_board[src] = 0
        return new_board

    # ========================================================================
    # Sea Current
    # ========================================================================

    def _current_destination(
        self,
        board: list[int],
        src: int,
        current: int,
    ) -> int:
        row, col = self._coord(src)

        if col != 2 or current == self._CURRENT_NONE:
            return src

        if current == self._CURRENT_UP:
            dr = -1
        elif current == self._CURRENT_DOWN:
            dr = 1
        else:
            raise ValueError("Invalid sea-current direction")

        # Move as far as possible until blocked by another piece or edge.
        while (
            self._on_board(row + dr, col)
            and board[self._index(row + dr, col)] == self._EMPTY
        ):
            row += dr

        return self._index(row, col)
        
    # ====================================================================
    # Primitive Helpers
    # ====================================================================    
    def _has_three_shrimps(self, board: list[int], player: int) -> bool:
        shrimp = self._shrimp_piece(player)
        return sum(piece == shrimp for piece in board) >= 3

    def _captured_three(self, board: list[int], player: int) -> bool:
        """Each player begins with 5 pieces and pieces never return."""
        opponent = 3 - player
        opponent_pieces_left = sum(
            self._owner(piece) == opponent for piece in board
        )
        return opponent_pieces_left <= 2

    def _has_any_normal_move(self, board: list[int], player: int) -> bool:
        for src, piece in enumerate(board):
            if self._owner(piece) != player:
                continue

            if self._normal_destinations(board, src):
                return True

        return False

    def _wins_immediately(self, board: list[int], player: int) -> bool:
        return (
            self._has_three_shrimps(board, player)
            or self._captured_three(board, player)
            or not self._has_any_normal_move(board, 3 - player)
        )

    # =======================================================================================
    # String Helpers
    # =======================================================================================

    def _board_to_chars(self, board: list[int]) -> str:
        return "".join(self._PIECE_TO_CHAR[piece] for piece in board)

    def _chars_to_board(self, chars: str) -> list[int]:
        if len(chars) != self._BOARD_SIZE:
            raise ValueError("Board string must contain exactly 25 squares")

        try:
            return [self._CHAR_TO_PIECE[c] for c in chars]
        except KeyError as exc:
            raise ValueError(f"Invalid board character: {exc.args[0]}") from exc

    # ========================================================================
    # Promotion / current branching
    # ========================================================================

    def _expand_landing(
        self,
        board: list[int],
        src: int,
        dest: int,
        player: int,
    ) -> list[tuple[list[int], int, int, bool]]:
        """Apply src->dest, then enumerate current and promotion choices.

        Returns tuples:
            (result_board, final_square, current_code, promote)

        Capture is NOT resolved here.
        """
        moved_board = self._move_piece(board, src, dest)

        # If movement initially stops in the middle column, player MUST choose
        # UP or DOWN. Both choices are legal even if one results in no movement.
        if self._coord(dest)[1] == 2:
            current_choices = (self._CURRENT_UP, self._CURRENT_DOWN)
        else:
            current_choices = (self._CURRENT_NONE,)

        results = []

        for current in current_choices:
            after_current = moved_board.copy()
            final_square = dest

            if current != self._CURRENT_NONE:
                final_square = self._current_destination(
                    after_current, dest, current
                )

                if final_square != dest:
                    after_current = self._move_piece(
                        after_current, dest, final_square
                    )

            piece = after_current[final_square]
            can_promote = (
                self._is_crab(piece)
                and self._coord(final_square)[1]
                == self._opponent_home_col(player)
            )

            # Promotion is optional.
            if can_promote:
                results.append(
                    (after_current.copy(), final_square, current, False)
                )

                promoted = after_current.copy()
                promoted[final_square] = self._shrimp_piece(player)
                results.append((promoted, final_square, current, True))
            else:
                results.append(
                    (after_current.copy(), final_square, current, False)
                )

        return results

        # ========================================================================
    # Bond -- STANDARD RULE: SAME TYPE ONLY
    # ========================================================================

    def _same_type_bond_group(
        self,
        board: list[int],
        start: int,
    ) -> set[int]:
        """Return same-player, SAME-PIECE-TYPE orthogonal component.

        Because piece equality is required, a Crab can only connect to Crabs
        belonging to the same player, and likewise for Shrimps.
        """
        piece = board[start]
        if piece == self._EMPTY:
            return set()

        visited = {start}
        stack = [start]

        while stack:
            current = stack.pop()
            row, col = self._coord(current)

            for dr, dc in self._ORTHOGONAL:
                new_row = row + dr
                new_col = col + dc

                if not self._on_board(new_row, new_col):
                    continue

                neighbor = self._index(new_row, new_col)

                # Exact piece equality is what enforces same-type Bonding.
                if neighbor not in visited and board[neighbor] == piece:
                    visited.add(neighbor)
                    stack.append(neighbor)

        return visited

    # ========================================================================
    # Bond -- MIXED RULE: ANY TYPE
    # ========================================================================

    def _mixed_bond_group(
        self,
        board: list[int],
        start: int,
    ) -> set[int]:
        """Return same-player orthogonal component (Crabs and Shrimps)."""
        piece = board[start]
        if piece == self._EMPTY:
            return set()
            
        player = self._owner(piece)
        visited = {start}
        stack = [start]

        while stack:
            current = stack.pop()
            row, col = self._coord(current)

            for dr, dc in self._ORTHOGONAL:
                new_row = row + dr
                new_col = col + dc

                if not self._on_board(new_row, new_col):
                    continue

                neighbor = self._index(new_row, new_col)

                # Check ownership rather than exact piece equality
                if neighbor not in visited and self._owner(board[neighbor]) == player:
                    visited.add(neighbor)
                    stack.append(neighbor)

        return visited

    # ========================================================================
    # Capture
    # ========================================================================

    def _resolve_captures(
        self,
        board: list[int],
        moved_piece_square: int,
        player: int,
    ) -> list[int]:
        """Capture every opponent chain sandwiched by moved piece + friendly.

        Only rows/columns count. Multiple sets can be captured at once.
        """
        new_board = board.copy()
        start_row, start_col = self._coord(moved_piece_square)
        captured: set[int] = set()

        for dr, dc in self._ORTHOGONAL:
            row = start_row + dr
            col = start_col + dc
            opponent_line: list[int] = []

            while self._on_board(row, col):
                square = self._index(row, col)
                square_owner = self._owner(new_board[square])

                # Keep scanning through a contiguous opponent chain.
                if square_owner == 3 - player:
                    opponent_line.append(square)
                    row += dr
                    col += dc
                    continue

                # Chain is captured only if closed by one of our pieces.
                if square_owner == player and opponent_line:
                    captured.update(opponent_line)

                # Empty square or friendly piece ends this direction scan.
                break

        for square in captured:
            new_board[square] = self._EMPTY

        return new_board

    # ====================================================================================================================
    # GamesCrafters Functions
    # ====================================================================================================================
    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in self.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        

        pass

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        board = [self._EMPTY] * self._BOARD_SIZE

        for row in range(self._ROWS):
            board[self._index(row, 0)] = self._P1_CRAB
            board[self._index(row, 4)] = self._P2_CRAB

        return self._hash_position(board, 1)        
        pass
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        board, player = self._unhash_position(position)

        # Do not generate moves from an already-finished position.
        previous_player = 3 - player
        if (
            self._has_three_shrimps(board, previous_player)
            or self._captured_three(board, previous_player)
        ):
            return []

        moves: list[int] = []

        # --------------------------------------------------------------------
        # 1. Generate every legal NORMAL movement.
        # --------------------------------------------------------------------
        for src, piece in enumerate(board):
            if self._owner(piece) != player:
                continue

            for dest in self._normal_destinations(board, src):

                # ----------------------------------------------------------------
                # 2. Branch on current direction and optional promotion.
                # ----------------------------------------------------------------
                for (
                    after_landing,
                    final_square,
                    current,
                    promote,
                ) in self._expand_landing(board, src, dest, player):

                    main_part = self._pack_part(
                        src, dest, current, promote
                    )

                    # Bond is checked AFTER sea current and promotion.
                    # Exact-piece equality means only same-type Bonding.
                    # Checks _variant_id to see if Mixed Bonding is enabled
                    if self._variant_id == "mixed":
                        bond_group = self._mixed_bond_group(after_landing, final_square)
                    else:
                        bond_group = self._same_type_bond_group(after_landing, final_square)

                    
                    # Main-move capture happens before the optional bonus move.
                    after_capture = self._resolve_captures(
                        after_landing, final_square, player
                    )

                    # The player may always stop after the main move.
                    moves.append(self._pack_move(main_part))

                    # Game ends immediately if a win condition was reached.
                    if self._wins_immediately(after_capture, player):
                        continue

                    # No Bond unless moved piece belongs to a same-type
                    # orthogonally connected group of size >= 2.
                    if len(bond_group) < 2:
                        continue

                    # ----------------------------------------------------------------
                    # 3. Optional Bond bonus:
                    #    choose ANY piece in that same-type group and move it
                    #    exactly one square diagonally.
                    # ----------------------------------------------------------------
                    for bond_src in sorted(bond_group):
                        for bond_dest in self._bond_destinations(
                            after_capture, bond_src
                        ):

                            # Bonus move also branches on current/promotion.
                            for (
                                _after_bond_landing,
                                _bond_final_square,
                                bond_current,
                                bond_promote,
                            ) in self._expand_landing(
                                after_capture,
                                bond_src,
                                bond_dest,
                                player,
                            ):
                                bond_part = self._pack_part(
                                    bond_src,
                                    bond_dest,
                                    bond_current,
                                    bond_promote,
                                )

                                moves.append(
                                    self._pack_move(main_part, bond_part)
                                )

        # A few distinct player choices can theoretically lead to duplicate
        # encoded moves; preserve order while removing duplicates.
        return list(dict.fromkeys(moves))
        pass

    def _apply_part(self, board: list[int], part_code: int, player: int) -> list[int]:
        src, dest, current, promote = self._unpack_part(part_code)

        new_board = self._move_piece(board, src, dest)
        final_square = dest

        # Sea current.
        if current != self._CURRENT_NONE:
            final_square = self._current_destination(
                new_board, dest, current
            )

            if final_square != dest:
                new_board = self._move_piece(
                    new_board, dest, final_square
                )

        # Optional promotion.
        if promote:
            new_board[final_square] = self._shrimp_piece(player)

        # Deterministic capture.
        new_board = self._resolve_captures(
            new_board, final_square, player
        )

        return new_board

    def do_move(self, position: int, move: int) -> int:
        board, player = self._unhash_position(position)
        main_part, bond_part = self._unpack_move(move)

        new_board = self._apply_part(board, main_part, player)

        # A generated move will never contain Bond after an immediate win,
        # but this guard makes do_move robust on manually constructed moves.
        if bond_part is not None and not self._wins_immediately(new_board, player):
            new_board = self._apply_part(
                new_board, bond_part, player
            )

        return self._hash(new_board, 3 - player)
    # def do_move(board: list[int], src: int, dest: int) -> list[int]:
    #     """
    #     Returns the resulting position of applying move to position.
    #     """
        
    #     new_board = board.copy()
    #     new_board[dest] = new_board[src]
    #     new_board[src] = 0
    #     return new_board
    #     pass

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        board, current_player = self._unhash_position(position)
        previous_player = 3 - current_player

        # If the player who just moved reached either material win condition,
        # the current player is in a losing terminal position.
        if self._has_three_shrimps(board, previous_player):
            return Value.Loss

        if self._captured_three(board, previous_player):
            return Value.Loss

        # Third win condition: current player has no legal normal move.
        if not self._has_any_normal_move(board, current_player):
            return Value.Loss

        return None        
        pass

    # hash current position into printable String board representation
    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        board, turn = self._unhash_position(position)
        chars = self._board_to_chars(board)

        if mode == StringMode.AUTOGUI:
            return f"{turn}_{chars}"

        if mode == StringMode.TUI:
            rows = [chars[r * 5:(r + 1) * 5] for r in range(5)]
            return "\n".join(rows) + f"\nturn={turn}"

        if mode == StringMode.Readable:
            return f"{chars}|{turn}"

    # unhash String board representation to the actual position
    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        # src, dest, current, promote = self._unpack_part(part_code)

        # text = f"{self._square_name(src)}->{self._square_name(dest)}"

        # if current == self._CURRENT_UP:
        #     text += " current = up"
        # elif current == self._CURRENT_DOWN:
        #     text += " current = down"

        # if promote:
        #     text += " promote"

        # return text

        try:
            chars, turn_str = strposition.split("|")
            turn = int(turn_str)
        except Exception as exc:
            raise ValueError(
                "Readable position must have format '<25 board chars>|<turn>'"
            ) from exc

        if turn not in (1, 2):
            raise ValueError("Turn must be 1 or 2")

        board = self._chars_to_board(chars)
        return self._hash(board, turn)
        pass

    # converts a move to a String 
    # Convert binary move representation to a string move
    # ex. 0b01110101110 -> "b2-2-u-d1-3-d"
    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        # Solver representation is a complete-turn move. For now return a
        # readable multipart description for all modes. A dedicated AutoGUI
        # half-move layer can be added later without changing solver logic.
        main_part, bond_part = self._unpack_move(move)
        #main_part -> bits of main part of move
        #bond_part -> bits of bond part of move

        text = self._part_to_string(main_part)

        if bond_part is not None:
            text += " ; BOND " + self._part_to_string(bond_part)

        return text
        pass
    
    