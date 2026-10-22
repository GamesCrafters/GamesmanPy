"""Boop game adapter and text display. Copy into games/src/games/boop.py.

Variant: 4x4, three active pieces per player. Place, boop, then resolve only the active player?s win or graduation.
render_options(position, lookup) accepts an optional database lookup taking an
integer position and returning (remoteness, Value), Value, or None, from the
next player's perspective. Displayed distances include the selected move.
Without a lookup, only immediate terminal outcomes are known; others are unsolved.
This module does not perform an exhaustive solve or define an AutoGUI layout.
"""

from typing import Callable, Optional
from functools import lru_cache
import math
import os
import sys
import time

from models import Game, Value, StringMode


class Boop(Game):
    id = "boop"
    variants = ["4x4-3pieces-original"]
    n_players = 2
    cyclic = True
    uses_half_moves = False
    SIZE = 4
    PIECES = 3
    CELLS = SIZE * SIZE
    PLACEMENTS = 2 * CELLS
    SUPPLY_BASE = PIECES + 1
    HASH_TAG = 3 << 60
    POSITION_LIMIT = 5 ** CELLS * SUPPLY_BASE ** 4 * 2
    # Empty, player 1 kitten/cat, player 2 kitten/cat.
    SYMBOLS = ".kKlL"
    LABELS = (" .", "K1", "C1", "K2", "C2")
    DIRECTIONS = tuple((dx, dy) for dx in (-1, 0, 1)
                       for dy in (-1, 0, 1) if dx or dy)

    def __init__(self, variant_id: str = "4x4-3pieces-original"):
        if variant_id not in self.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._cached_position = None
        self._cached_children = {}
        self._progress_interval = float(os.environ.get("BOOP_PROGRESS_SECONDS", "0"))
        if not math.isfinite(self._progress_interval) or self._progress_interval < 0:
            raise ValueError("BOOP_PROGRESS_SECONDS must be a finite nonnegative number")
        self._progress_started = None
        self._progress_last = 0.0
        self._progress_expanded = 0
        self._progress_moves = 0
        self._symmetry_weights = []
        for reflected in (False, True):
            for rotations in range(4):
                weights = []
                for square in range(self.CELLS):
                    column, row = square % self.SIZE, square // self.SIZE
                    if reflected:
                        column = self.SIZE - 1 - column
                    for _ in range(rotations):
                        column, row = self.SIZE - 1 - row, column
                    destination = row * self.SIZE + column
                    weights.append(5 ** (self.CELLS - 1 - destination))
                self._symmetry_weights.append(tuple(weights))
        self._row_hash_tables, self._row_piece_counts = self._build_hash_tables(
            self.SIZE, tuple(self._symmetry_weights))
        self._lines = []
        for y in range(self.SIZE):
            for x in range(self.SIZE):
                for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                    if 0 <= x + 2 * dx < self.SIZE and 0 <= y + 2 * dy < self.SIZE:
                        self._lines.append(tuple((y + n * dy) * self.SIZE + x + n * dx
                                                 for n in range(3)))
        self._line_masks = tuple(sum(1 << square for square in line) for line in self._lines)
        self._board_weights = tuple(5 ** (self.CELLS - 1 - square) for square in range(self.CELLS))
        self._boop_targets = []
        for square in range(self.CELLS):
            column, row = square % self.SIZE, square // self.SIZE
            targets = []
            for dx, dy in self.DIRECTIONS:
                adjacent_column, adjacent_row = column + dx, row + dy
                if not (0 <= adjacent_column < self.SIZE and 0 <= adjacent_row < self.SIZE):
                    continue
                destination_column, destination_row = column + 2 * dx, row + 2 * dy
                destination = (1 << (destination_row * self.SIZE + destination_column)
                               if 0 <= destination_column < self.SIZE and 0 <= destination_row < self.SIZE
                               else 0)
                targets.append((1 << (adjacent_row * self.SIZE + adjacent_column), destination))
            self._boop_targets.append(tuple(targets))

    @staticmethod
    def _owner(piece):
        return (piece + 1) // 2

    def _pack(self, board, supply, turn):
        position = 0
        for piece in board:
            position = position * 5 + piece
        for count in supply:
            position = position * self.SUPPLY_BASE + count
        return position * 2 + turn - 1

    def _unpack(self, position):
        if not isinstance(position, int) or position < 0:
            raise ValueError("Position must be a nonnegative integer")
        position, turn = divmod(position, 2)
        supply = [0] * 4
        for i in range(3, -1, -1):
            position, supply[i] = divmod(position, self.SUPPLY_BASE)
        board = [0] * self.CELLS
        for i in range(self.CELLS - 1, -1, -1):
            position, board[i] = divmod(position, 5)
        if position:
            raise ValueError("Position is too large")
        for player in (1, 2):
            if (sum(Boop._owner(p) == player for p in board)
                    + sum(supply[(player - 1) * 2:player * 2]) != self.PIECES):
                raise ValueError("Each player must have exactly three active pieces")
        return board, supply, turn + 1

    def start(self) -> int:
        return self._pack([0] * self.CELLS, [self.PIECES, 0, self.PIECES, 0], 1)

    @staticmethod
    @lru_cache(maxsize=1)
    def _build_hash_tables(size, symmetry_weights):
        """Fixed-size tables shared between instances, independent of explored states."""
        rows = []
        counts = []
        for code in range(5 ** size):
            digits = [0] * size
            remaining = code
            for column in range(size - 1, -1, -1):
                remaining, digits[column] = divmod(remaining, 5)
            rows.append(tuple(digits))
            counts.append((sum(piece in (1, 2) for piece in digits),
                           sum(piece in (3, 4) for piece in digits)))
        tables = tuple(
            tuple(tuple(sum(piece * weights[row * size + column]
                            for column, piece in enumerate(digits))
                        for weights in symmetry_weights)
                  for digits in rows)
            for row in range(size))
        return tables, tuple(counts)

    def hash_ext(self, position: int) -> int:
        """Share a SQLite key across the eight square-board symmetries.

        Supplies, piece types, owners, and turn are preserved. The live position
        and displayed moves retain their original orientation. The tag separates
        these keys from the previous database encoding; rebuild old databases.
        """
        if not isinstance(position, int) or not 0 <= position < self.POSITION_LIMIT:
            raise ValueError("Position must be a valid nonnegative Boop integer")
        factor = self.SUPPLY_BASE ** 4 * 2
        board_code, metadata = divmod(position, factor)
        contributions = []
        first_count = second_count = 0
        for table in reversed(self._row_hash_tables):
            board_code, row_code = divmod(board_code, 5 ** self.SIZE)
            contributions.append(table[row_code])
            first, second = self._row_piece_counts[row_code]
            first_count += first
            second_count += second
        remaining = metadata // 2
        remaining, second_cats = divmod(remaining, self.SUPPLY_BASE)
        remaining, second_kittens = divmod(remaining, self.SUPPLY_BASE)
        first_kittens, first_cats = divmod(remaining, self.SUPPLY_BASE)
        if (first_count + first_kittens + first_cats != self.PIECES
                or second_count + second_kittens + second_cats != self.PIECES):
            raise ValueError("Each player must have exactly three active pieces")
        canonical_board = min(map(sum, zip(*contributions)))
        occupied = codes = count = 0
        for square in range(self.CELLS - 1, -1, -1):
            canonical_board, piece = divmod(canonical_board, 5)
            if piece:
                occupied |= 1 << square
                codes |= (piece - 1) << (2 * count)
                count += 1
        return self.HASH_TAG + ((codes << self.CELLS) | occupied) * factor + metadata

    def unhash_ext(self, hashed_pos: int) -> int:
        """Return the canonical board represented by a compact symmetry key."""
        limit = (1 << (self.CELLS + 4 * self.PIECES)) * self.SUPPLY_BASE ** 4 * 2
        if not isinstance(hashed_pos, int) or not self.HASH_TAG <= hashed_pos < self.HASH_TAG + limit:
            raise ValueError("Invalid custom Boop database key")
        payload, metadata = divmod(hashed_pos - self.HASH_TAG, self.SUPPLY_BASE ** 4 * 2)
        occupied = payload & ((1 << self.CELLS) - 1)
        codes = payload >> self.CELLS
        if occupied.bit_count() > 2 * self.PIECES:
            raise ValueError("Too many pieces in database key")
        board_code = 0
        for square in range(self.CELLS - 1, -1, -1):
            if occupied & (1 << square):
                board_code += ((codes & 3) + 1) * self._board_weights[square]
                codes >>= 2
        if codes:
            raise ValueError("Unused piece bits in database key")
        position = board_code * self.SUPPLY_BASE ** 4 * 2 + metadata
        self._unpack(position)
        if self.hash_ext(position) != hashed_pos:
            raise ValueError("Database key is not canonical")
        return position

    def database_lookup(self, connection):
        """Return (remoteness, Value) from the child's side-to-move perspective.

        The caller owns the connection. Missing rows remain UNSOLVED.
        """
        def lookup(position):
            row = connection.execute(
                "SELECT remoteness, value FROM gamedb WHERE state = ?",
                (self.hash_ext(position),),
            ).fetchone()
            return None if row is None else (row[0], Value(row[1]))
        return lookup

    def _wins(self, board, player):
        cat = player * 2
        return (board.count(cat) == self.PIECES
                or any(all(board[i] == cat for i in line) for line in self._lines))

    def primitive(self, position: int) -> Optional[Value]:
        board, _, turn = self._unpack(position)
        # Every encoded move completes a turn, so a mover's win is a loss
        # for the player to move. Check the previous player first.
        if self._wins(board, 3 - turn):
            return Value.Loss
        return None



    def generate_moves(self, position: int) -> list[int]:
        """Keep one position's successors for the original solver's do_move calls."""
        if not isinstance(position, int) or position != self._cached_position:
            if self._progress_interval and self._progress_started is None:
                self._progress_started = self._progress_last = time.perf_counter()
                print("[Boop] Activity reporting enabled; visited total, queue size, and ETA are unavailable.",
                      file=sys.stderr, flush=True)
            children = dict(self.generate_successors(position))
            self._cached_position = position
            self._cached_children = children
            if self._progress_interval:
                self._progress_expanded += 1
                self._progress_moves += len(children)
                now = time.perf_counter()
                if now - self._progress_last >= self._progress_interval:
                    elapsed = now - self._progress_started
                    rate = self._progress_expanded / elapsed if elapsed else 0
                    print(f"[Boop] elapsed={elapsed:,.1f}s | expansions={self._progress_expanded:,} | "
                          f"moves generated={self._progress_moves:,} | expansions/s={rate:,.0f}",
                          file=sys.stderr, flush=True)
                    self._progress_last = now
        return list(self._cached_children)

    def generate_successors(self, position: int):
        """Generate successors using four bitboards, retaining the position encoding."""
        board, supply, turn = self._unpack(position)

        masks = [0, 0, 0, 0]
        for square, piece in enumerate(board):
            if piece:
                masks[piece - 1] |= 1 << square

        if self._cats_win_bits(masks[(2 - turn) * 2 + 1]):
            return

        occupied = masks[0] | masks[1] | masks[2] | masks[3]
        empty = ((1 << self.CELLS) - 1) ^ occupied
        owner_offset = (turn - 1) * 2

        for kind in (0, 1):
            piece_index = owner_offset + kind

            if supply[piece_index] == 0:
                continue

            remaining = empty

            while remaining:
                placement = remaining & -remaining
                remaining ^= placement

                square = placement.bit_length() - 1

                after, after_supply = masks.copy(), supply.copy()


                after[piece_index] |= placement
                after_supply[piece_index] -= 1

                for source, destination in self._boop_targets[square]:

                    if not occupied & source:
                        continue

                    if occupied & destination:
                        continue

                    for target_index in range(4):
                        if masks[target_index] & source:

                            # A kitten cannot boop a cat.
                            if kind == 0 and target_index % 2:
                                break

                            after[target_index] ^= source
                            after[target_index] |= destination

                            # Piece was booped off the board.
                            if destination == 0:
                                after_supply[target_index] += 1

                            break



                base_move = square + self.CELLS * kind
                if self._cats_win_bits(after[owner_offset + 1]):
                    yield base_move, self._pack_bits(after, after_supply, 3 - turn)
                    continue

                own = after[owner_offset] | after[owner_offset + 1]
                choices = [line for line in self._line_masks if own & line == line]
                if own.bit_count() == self.PIECES:
                    choices.extend(1 << i for i in range(self.CELLS) if own & (1 << i))
                if not choices:
                    yield base_move, self._pack_bits(after, after_supply, 3 - turn)
                for selected in choices:
                    graduated = after.copy()
                    graduated[owner_offset] &= ~selected
                    graduated[owner_offset + 1] &= ~selected
                    reserves = after_supply.copy()
                    reserves[owner_offset + 1] += selected.bit_count()
                    move = base_move + self.PLACEMENTS * selected
                    yield move, self._pack_bits(graduated, reserves, 3 - turn)

    def _cats_win_bits(self, cats):
        return cats.bit_count() == self.PIECES or any(
            cats & line == line for line in self._line_masks)



    def _pack_bits(self, masks, supply, turn):
        position = 0
        for piece, mask in enumerate(masks, 1):
            while mask:
                occupied = mask & -mask
                mask ^= occupied
                position += piece * self._board_weights[occupied.bit_length() - 1]
        for count in supply:
            position = position * self.SUPPLY_BASE + count
        return position * 2 + turn - 1

    def do_move(self, position: int, move: int) -> int:
        if not isinstance(move, int) or move < 0:
            raise ValueError("Invalid move")
        self.generate_moves(position)
        if move not in self._cached_children:
            raise ValueError("Illegal move")
        return self._cached_children[move]

    def to_string(self, position: int, mode: StringMode) -> str:
        board, supply, turn = self._unpack(position)
        if mode == StringMode.Readable:
            return f"{turn}|{''.join(self.SYMBOLS[p] for p in board)}|" + ",".join(map(str, supply))
        if mode == StringMode.AUTOGUI:
            cells = "".join(self.SYMBOLS[p] if p else "-" for p in board)
            p1 = ("k" * supply[0] + "K" * supply[1]).ljust(self.PIECES, "-")
            p2 = ("l" * supply[2] + "L" * supply[3]).ljust(self.PIECES, "-")
            return f"{turn}_{cells}{p1}{p2}" + "-" * 56
        if mode != StringMode.TUI:
            raise ValueError("Unknown string mode")
        border = "    +" + "---+" * self.SIZE
        rows = ["Boop 4x4 - three pieces per player", f"TURN: Player {turn} (K{turn} / C{turn})",
                "      A   B   C   D", border]
        for y in reversed(range(self.SIZE)):
            rows.append(f" {y + 1}  |" + "|".join(f"{self.LABELS[p]} " for p in board[y * self.SIZE:(y + 1) * self.SIZE]) + f"| {y + 1}")
            rows.append(border)
        rows += ["      A   B   C   D",
                 "K = kitten; C = cat; number = owner; A1 is bottom left",
                 f"Player 1 off-board: {supply[0]} kittens (K), {supply[1]} cats (C)",
                 f"Player 2 off-board: {supply[2]} kittens (K), {supply[3]} cats (C)"]
        return "\n".join(rows)

    def from_string(self, strposition: str) -> int:
        try:
            player, cells, counts = strposition.strip().split("|")
            turn = int(player)
            board = [self.SYMBOLS.index(c) for c in cells]
            supply = [int(c) for c in counts.split(",")]
            if turn not in (1, 2) or len(board) != self.CELLS or len(supply) != 4:
                raise ValueError()
            if any(not 0 <= count <= self.PIECES for count in supply):
                raise ValueError()
            position = self._pack(board, supply, turn)
            self._unpack(position)
            return position
        except (ValueError, TypeError) as error:
            raise ValueError("Expected turn|16 board symbols (.kKlL)|p1k,p1c,p2k,p2c, with three pieces per player") from error

    def move_to_string(self, move: int, mode: StringMode) -> str:
        if mode == StringMode.AUTOGUI:
            selected, base = divmod(move, self.PLACEMENTS)
            kind, square = divmod(base, self.CELLS)
            if not selected:
                return f"A_{'ab'[kind]}_{(22, 38)[kind] + square}_x"
            return f"A_{'ab'[kind]}_{square}_x"
        if mode not in (StringMode.Readable, StringMode.TUI):
            raise ValueError("Unknown string mode")
        if not isinstance(move, int) or move < 0:
            raise ValueError("Invalid move")
        selected, base = divmod(move, self.PLACEMENTS)
        if selected >= 1 << self.CELLS:
            raise ValueError("Invalid graduation squares")
        kind, square = divmod(base, self.CELLS)
        label = f"{('K', 'C')[kind]} {self._coordinate(square)}"
        if selected:
            label += " / " + " ".join(self._coordinate(i) for i in range(self.CELLS)
                                      if selected & (1 << i))
        return label

    def _coordinate(self, square: int) -> str:
        return f"{chr(ord('A') + square % self.SIZE)}{square // self.SIZE + 1}"

    def _square(self, coordinate: str) -> int:
        coordinate = coordinate.upper()
        if (len(coordinate) != 2 or coordinate[0] not in "ABCD"
                or coordinate[1] not in "1234"):
            raise ValueError("Use a square from A1 to D4")
        return (int(coordinate[1]) - 1) * self.SIZE + ord(coordinate[0]) - ord('A')

    def move_from_string(self, position: int, text: str) -> int:
        """Accept a list number or placement with optional graduation squares."""
        text = text.strip().lower()
        moves = self.generate_moves(position)
        if text.isascii() and text.isdecimal():
            number = int(text)
            if not 1 <= number <= len(moves):
                raise ValueError("Choose a move number from the list")
            return moves[number - 1]
        placement, separator, graduation = text.partition("/")
        selected = None
        if separator:
            squares = graduation.split()
            if not squares:
                raise ValueError("List the graduation squares after /")
            selected = 0
            for coordinate in squares:
                selected |= 1 << self._square(coordinate)
        tokens = placement.split()
        kinds = {"k": 0, "kitten": 0, "c": 1, "cat": 1}
        kind = None
        if len(tokens) == 1:
            square = self._square(tokens[0])
        elif len(tokens) == 2 and tokens[0] in kinds:
            kind = kinds[tokens[0]]
            square = self._square(tokens[1])
        else:
            raise ValueError("Use K A1 or C A1, optionally / followed by graduation squares")
        matches = [move for move in moves
                   if move % self.PLACEMENTS % self.CELLS == square
                   and (kind is None or move % self.PLACEMENTS // self.CELLS == kind)
                   and (selected is None or move // self.PLACEMENTS == selected)]
        if not matches:
            raise ValueError("That move is not legal; choose from the list")
        if len(matches) > 1:
            raise ValueError("Choose a listed move number, or specify piece and / graduation squares")
        return matches[0]

    def render_options(self, position: int,
                       lookup: Optional[Callable[[int], Optional[Value | tuple[int, Value]]]] = None) -> str:
        """Draw the board and all moves; lookup values are for child side to move.

        This helper is for a text caller. The framework will not automatically
        call it; the standard methods above remain available to its own UI.
        """
        rows = [self.to_string(position, StringMode.TUI), ""]
        terminal = self.primitive(position)
        if terminal is not None:
            rows.append(f"Game over: {terminal.name.lower()} for the player to move.")
            return "\n".join(rows)
        labels = {Value.Loss: "WIN", Value.Win: "LOSS",
                  Value.Tie: "TIE", Value.Draw: "DRAW"}
        rows.append("Legal moves - outcomes for the player choosing the move:")
        rows.append("Enter a listed move number (e.g. 7) or a square (e.g. A1).")
        rows.append("Use K A1 or C A1; / lists pieces retrieved after booping. Choose a move number when ambiguous.")
        for number, (move, child) in enumerate(self.generate_successors(position), 1):
            value = self.primitive(child)
            immediate = value is not None
            distance = 0 if immediate else None
            if value is None and lookup is not None:
                result = lookup(child)
                if isinstance(result, tuple) and len(result) == 2:
                    distance, value = result
                    if not isinstance(distance, int) or distance < 0:
                        raise TypeError("Remoteness must be a nonnegative integer")
                else:
                    value = result
                if value is not None and not isinstance(value, Value):
                    raise TypeError("lookup must return (remoteness, Value), Value, or None")
            label = "UNSOLVED" if value is None else labels[value]
            if value == Value.Draw:
                label += " in 255 moves"
            elif value in (Value.Win, Value.Loss, Value.Tie) and distance is not None:
                moves_left = distance + 1
                label += f" in {moves_left} {'move' if moves_left == 1 else 'moves'}"
            if immediate:
                label += " (immediate)"
            rows.append(f"{number:3}. [{label}] {self.move_to_string(move, StringMode.TUI)}")
        return "\n".join(rows)


def main():
    import argparse
    import importlib.util
    from pathlib import Path
    import sqlite3

    parser = argparse.ArgumentParser(description="Play 4x4 Boop with saved solver values")
    parser.add_argument("--db", type=Path, help="Path to the solved boop_4x4-3pieces-original.db")
    args = parser.parse_args()
    game = Boop("4x4-3pieces-original")
    position = game.start()
    path = args.db
    if path is None:
        spec = importlib.util.find_spec("database")
        if spec is not None and spec.origin:
            path = Path(spec.origin).resolve().parents[2] / "db" / "boop_4x4-3pieces-original.db"
    connection = lookup = None
    if path is not None and path.is_file():
        try:
            connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
            lookup = game.database_lookup(connection)
            if lookup(position) is None:
                print("Database is incomplete or uses an older encoding; missing results show UNSOLVED.")
            else:
                print(f"Reading solution values from {path}")
        except (sqlite3.Error, ValueError) as error:
            print(f"Cannot read solution database: {error}")
            if connection is not None:
                connection.close()
            connection = lookup = None
    else:
        print("No solution database found; nonterminal moves show UNSOLVED.")
    try:
        while True:
            print(game.render_options(position, lookup))
            if game.primitive(position) is not None:
                break
            _, _, turn = game._unpack(position)
            try:
                raw = input(f"Player {turn}, enter move number or coordinates (7, A1, K B2, C C3), or q: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if raw.lower() in ("q", "quit", "exit"):
                break
            try:
                position = game.do_move(position, game.move_from_string(position, raw))
            except ValueError as error:
                print(error)
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
