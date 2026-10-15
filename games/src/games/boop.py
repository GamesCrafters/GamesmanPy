"""Boop game adapter and text display. Copy into games/src/games/boop.py.

Variant: 4x4, five active pieces per player. Complete moves include any required graduation choice.
render_options(position, lookup) accepts an optional database lookup taking an
integer position and returning Value or None, from the next player's perspective.
Without a lookup, only immediate terminal outcomes are known; others are unsolved.
This module does not perform an exhaustive solve or define an AutoGUI layout.
"""

from typing import Callable, Optional

from models import Game, Value, StringMode


class Boop(Game):
    id = "boop"
    variants = ["4x4"]
    n_players = 2
    cyclic = True
    uses_half_moves = False
    SIZE = 4
    PIECES = 5
    CELLS = SIZE * SIZE
    PLACEMENTS = 2 * CELLS
    SUPPLY_BASE = PIECES + 1
    HASH_TAG = (1 << 62) + (1 << 60)
    POSITION_LIMIT = 5 ** CELLS * SUPPLY_BASE ** 4 * 2
    # Empty, player 1 kitten/cat, player 2 kitten/cat.
    SYMBOLS = ".kKlL"
    LABELS = (" .", "K1", "C1", "K2", "C2")
    DIRECTIONS = tuple((dx, dy) for dx in (-1, 0, 1)
                       for dy in (-1, 0, 1) if dx or dy)

    def __init__(self, variant_id: str = "4x4"):
        if variant_id not in self.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
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
                raise ValueError("Each player must have exactly fi`ve active pieces")
        return board, supply, turn + 1

    def start(self) -> int:
        return self._pack([0] * self.CELLS, [self.PIECES, 0, self.PIECES, 0], 1)

    def hash_ext(self, position: int) -> int:
        """Share a SQLite key across the eight square-board symmetries.

        Supplies, piece types, owners, and turn are preserved. The live position
        and displayed moves retain their original orientation. The tag separates
        these keys from the previous database encoding; rebuild old databases.
        """
        board, supply, turn = self._unpack(position)
        occupied = [(square, piece) for square, piece in enumerate(board) if piece]
        payload = min(sum(piece * weights[square] for square, piece in occupied)
                      for weights in self._symmetry_weights)
        for amount in supply:
            payload = payload * self.SUPPLY_BASE + amount
        return self.HASH_TAG + payload * 2 + turn - 1

    def unhash_ext(self, hashed_pos: int) -> int:
        """Return the canonical orientation, not necessarily the original one."""
        if (not isinstance(hashed_pos, int)
                or not self.HASH_TAG <= hashed_pos < self.HASH_TAG + self.POSITION_LIMIT):
            raise ValueError("Not a symmetry-aware Boop database key")
        position = hashed_pos - self.HASH_TAG
        self._unpack(position)
        if self.hash_ext(position) != hashed_pos:
            raise ValueError("Database key is not in canonical orientation")
        return position

    def database_lookup(self, connection):
        """Adapt this repository's SQLite rows to child-position Value lookups.

        The caller owns the connection. Missing rows remain UNSOLVED.
        """
        def lookup(position):
            row = connection.execute(
                "SELECT value FROM gamedb WHERE state = ?",
                (self.hash_ext(position),),
            ).fetchone()
            return None if row is None else Value(row[0])
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
        if self._wins(board, turn):
            return Value.Win
        return None

    def _place(self, board, supply, turn, square, kind):
        board, supply = board.copy(), supply.copy()
        piece = (turn - 1) * 2 + kind + 1
        board[square] = piece
        supply[piece - 1] -= 1
        x, y = square % self.SIZE, square // self.SIZE
        # Each destination is two squares from the placement, so it cannot
        # be another adjacent piece's source. Snapshot checks suffice.
        before = board.copy()
        for dx, dy in self.DIRECTIONS:
            fx, fy = x + dx, y + dy
            if not (0 <= fx < self.SIZE and 0 <= fy < self.SIZE):
                continue
            source = fy * self.SIZE + fx
            target = before[source]
            if not target or (kind == 0 and target % 2 == 0):
                continue
            tx, ty = x + 2 * dx, y + 2 * dy
            if not (0 <= tx < self.SIZE and 0 <= ty < self.SIZE):
                board[source] = 0
                supply[target - 1] += 1
            elif before[ty * self.SIZE + tx] == 0:
                board[source] = 0
                board[ty * self.SIZE + tx] = target
        return board, supply

    def _choices(self, board, turn):
        if self._wins(board, turn) or self._wins(board, 3 - turn):
            return [0]
        # 0 = no graduation; 1..CELLS = single piece; CELLS+1 onward = line.
        choices = [self.CELLS + 1 + n for n, line in enumerate(self._lines)
                   if all(self._owner(board[i]) == turn for i in line)]
        owned = [i for i, piece in enumerate(board) if self._owner(piece) == turn]
        if len(owned) == self.PIECES:
            choices.extend(i + 1 for i in owned)
        return choices or [0]

    def generate_moves(self, position: int) -> list[int]:
        return [move for move, _ in self.generate_successors(position)]

    def generate_successors(self, position: int):
        """Generate successors using four bitboards, retaining the position encoding."""
        board, supply, turn = self._unpack(position)
        masks = [0, 0, 0, 0]
        for square, piece in enumerate(board):
            if piece:
                masks[piece - 1] |= 1 << square
        if self._cats_win_bits(masks[1]) or self._cats_win_bits(masks[3]):
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
                    if not occupied & source or occupied & destination:
                        continue
                    for target_index in range(4):
                        if masks[target_index] & source:
                            if kind == 0 and target_index % 2:
                                break
                            after[target_index] ^= source
                            after[target_index] |= destination
                            if destination == 0:
                                after_supply[target_index] += 1
                            break
                for choice, removal in self._bit_choices(after, owner_offset):
                    move = square + self.CELLS * kind + self.PLACEMENTS * choice
                    child_masks, child_supply = after, after_supply
                    if removal:
                        child_masks, child_supply = after.copy(), after_supply.copy()
                        child_masks[owner_offset] &= ~removal
                        child_masks[owner_offset + 1] &= ~removal
                        child_supply[owner_offset + 1] += removal.bit_count()
                    yield move, self._pack_bits(child_masks, child_supply, 3 - turn)

    def _cats_win_bits(self, cats):
        return cats.bit_count() == self.PIECES or any(
            cats & line == line for line in self._line_masks)

    def _bit_choices(self, masks, owner_offset):
        if self._cats_win_bits(masks[1]) or self._cats_win_bits(masks[3]):
            return [(0, 0)]
        owned = masks[owner_offset] | masks[owner_offset + 1]
        choices = [(self.CELLS + 1 + index, line)
                   for index, line in enumerate(self._line_masks) if owned & line == line]
        if owned.bit_count() == self.PIECES:
            while owned:
                piece = owned & -owned
                owned ^= piece
                choices.append((piece.bit_length(), piece))
        return choices or [(0, 0)]

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

    def _finish_turn(self, board, supply, turn, choice):
        if choice:
            board, supply = board.copy(), supply.copy()
            cells = (choice - 1,) if choice <= self.CELLS else self._lines[choice - self.CELLS - 1]
            for cell in cells:
                board[cell] = 0
            supply[(turn - 1) * 2 + 1] += len(cells)
        return self._pack(board, supply, 3 - turn)

    def do_move(self, position: int, move: int) -> int:
        if not isinstance(move, int) or move < 0:
            raise ValueError("Invalid move")
        if self.primitive(position) is not None:
            raise ValueError("Game has already ended")
        board, supply, turn = self._unpack(position)
        choice, placement = divmod(move, self.PLACEMENTS)
        kind, square = divmod(placement, self.CELLS)
        if board[square] or not supply[(turn - 1) * 2 + kind]:
            raise ValueError("Illegal placement")
        board, supply = self._place(board, supply, turn, square, kind)
        if choice not in self._choices(board, turn):
            raise ValueError("Illegal graduation choice")
        return self._finish_turn(board, supply, turn, choice)

    def to_string(self, position: int, mode: StringMode) -> str:
        board, supply, turn = self._unpack(position)
        if mode == StringMode.Readable:
            return f"{turn}|{''.join(self.SYMBOLS[p] for p in board)}|" + ",".join(map(str, supply))
        if mode == StringMode.AUTOGUI:
            raise NotImplementedError("Boop currently supports text display only")
        if mode != StringMode.TUI:
            raise ValueError("Unknown string mode")
        border = "    +" + "---+" * self.SIZE
        rows = ["Boop 4x4", f"TURN: Player {turn} (K{turn} / C{turn})",
                "      A   B   C   D", border]
        for y in reversed(range(self.SIZE)):
            rows.append(f" {y + 1}  |" + "|".join(f"{self.LABELS[p]} " for p in board[y * self.SIZE:(y + 1) * self.SIZE]) + f"| {y + 1}")
            rows.append(border)
        rows += ["      A   B   C   D",
                 "K = kitten; C = cat; number = owner; A1 is bottom left",
                 f"Player 1 supply: {supply[0]} kittens, {supply[1]} cats",
                 f"Player 2 supply: {supply[2]} kittens, {supply[3]} cats"]
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
            raise ValueError("Expected turn|16 board symbols (.kKlL)|p1k,p1c,p2k,p2c, with five pieces per player") from error

    def move_to_string(self, move: int, mode: StringMode) -> str:
        if mode == StringMode.AUTOGUI:
            raise NotImplementedError("Boop currently supports text display only")
        if mode not in (StringMode.Readable, StringMode.TUI):
            raise ValueError("Unknown string mode")
        if not isinstance(move, int) or move < 0:
            raise ValueError("Invalid move")
        choice, placement = divmod(move, self.PLACEMENTS)
        kind, square = divmod(placement, self.CELLS)
        # The displayed command is also accepted by move_from_string().
        description = f"{'C' if kind else 'K'} {self._coordinate(square)}"
        if 1 <= choice <= self.CELLS:
            cell = choice - 1
            description += f" / {self._coordinate(cell)}"
        elif choice > self.CELLS:
            if choice - self.CELLS - 1 >= len(self._lines):
                raise ValueError("Invalid graduation code")
            coords = " ".join(self._coordinate(i) for i in self._lines[choice - self.CELLS - 1])
            description += f" / {coords}"
        return description

    def _coordinate(self, square: int) -> str:
        return f"{chr(ord('A') + square % self.SIZE)}{square // self.SIZE + 1}"

    def _square(self, coordinate: str) -> int:
        coordinate = coordinate.upper()
        if (len(coordinate) != 2 or coordinate[0] not in "ABCD"
                or coordinate[1] not in "1234"):
            raise ValueError("Use a square from A1 to D4")
        return (int(coordinate[1]) - 1) * self.SIZE + ord(coordinate[0]) - ord('A')

    def move_from_string(self, position: int, text: str) -> int:
        """Parse a displayed move number, 'k A1', or 'k C1 / A1 B1 C1'.

        Move numbers are one-based indices into the current legal move list.
        A bare square is accepted when only one piece type is legal there.
        Graduation can be omitted only when the placement has one outcome.
        """
        text = text.strip().lower()
        moves = self.generate_moves(position)
        if text.isascii() and text.isdecimal():
            number = int(text)
            if not 1 <= number <= len(moves):
                raise ValueError(f"Choose a move number from 1 to {len(moves)}" if moves
                                 else "No legal moves: the game has ended")
            return moves[number - 1]
        parts = text.split("/")
        if len(parts) > 2:
            raise ValueError("Use k A1 or c A1, optionally / graduation squares")
        placement = parts[0].split()
        kind = None
        if len(placement) == 2 and placement[0] in ("k", "kitten", "c", "cat"):
            kind = int(placement[0] in ("c", "cat"))
            square = self._square(placement[1])
        elif len(placement) == 1:
            square = self._square(placement[0])
        else:
            raise ValueError("Use k A1 for a kitten or c A1 for a cat")
        graduation = None
        if len(parts) == 2:
            cells = [self._square(token) for token in parts[1].replace(",", " ").split()]
            if len(cells) not in (1, 3) or len(set(cells)) != len(cells):
                raise ValueError("Specify one or three distinct graduation squares after /")
            graduation = set(cells)
        matches = []
        for move in moves:
            choice, encoded = divmod(move, self.PLACEMENTS)
            move_kind, move_square = divmod(encoded, self.CELLS)
            if move_square != square or (kind is not None and kind != move_kind):
                continue
            cells = (set() if choice == 0 else {choice - 1} if choice <= self.CELLS
                     else set(self._lines[choice - self.CELLS - 1]))
            if graduation is None or graduation == cells:
                matches.append(move)
        if not matches:
            raise ValueError("That move is not legal; choose a command from the displayed list")
        if len(matches) != 1:
            options = "; ".join(self.move_to_string(m, StringMode.TUI) for m in matches)
            raise ValueError(f"Choose the piece type and graduation explicitly: {options}")
        return matches[0]

    def render_options(self, position: int,
                       lookup: Optional[Callable[[int], Optional[Value]]] = None) -> str:
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
        rows.append("Use K A1 (kitten) or C A1 (cat) to specify the piece; / marks graduation squares.")
        for number, (move, child) in enumerate(self.generate_successors(position), 1):
            value = self.primitive(child)
            immediate = value is not None
            if value is None and lookup is not None:
                value = lookup(child)
                if value is not None and not isinstance(value, Value):
                    raise TypeError("lookup must return Value or None")
            label = "UNSOLVED" if value is None else labels[value]
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
    parser.add_argument("--db", type=Path, help="Path to the solved boop_4x4.db")
    args = parser.parse_args()
    game = Boop("4x4")
    position = game.start()
    path = args.db
    if path is None:
        spec = importlib.util.find_spec("database")
        if spec is not None and spec.origin:
            path = Path(spec.origin).resolve().parents[2] / "db" / "boop_4x4.db"
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
