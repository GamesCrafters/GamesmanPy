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
    def _hash(self, board: list[int], turn: int) -> int:
        """Encode 25 squares using 3 bits each, plus 1 turn bit."""
        position = 0
        for i, piece in enumerate(board):
            position |= piece << (3 * i)

        # bit 75 (position bit): 0 => P1, 1 => P2
        position |= (turn - 1) << 75
        return position

    def _unhash(self, position: int) -> tuple[list[int], int]:
        board = [self._EMPTY] * self._BOARD_SIZE
        for i in range(self._BOARD_SIZE):
            board[i] = (position >> (3 * i)) & 0b111

        turn = ((position >> 75) & 1) + 1
        return board, turn

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

    # ====================================================================================================================
    # GamesCrafters Functions
    # ====================================================================================================================
    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Example.variants:
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

        return self._hash(board, 1)        
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

    
    def do_move(board: list[int], src: int, dest: int) -> list[int]:
        """
        Returns the resulting position of applying move to position.
        """
        new_board = board.copy()
        new_board[dest] = new_board[src]
        new_board[src] = 0
        return new_board
        pass

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        board, current_player = self._unhash(position)
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
        board_nums, turn = self._unhash(position)
        player = 3 - turn
        
        # todo note: convert board_nums into pos_str (go from # board -> char board. This is output)
        if mode == StringMode.AUTOGUI:
            autogui_player = '1_' if player == 1 else '2_'
            pos_str = autogui_player + pos_str
        elif mode == StringMode.Readable:

        return pos_str
        pass

    # unhash String board representation to the actual position
    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
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

        text = self._part_to_string(main_part)

        if bond_part is not None:
            text += " ; BOND " + self._part_to_string(bond_part)

        return text
        pass
    
    