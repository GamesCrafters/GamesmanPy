"""
Boop - text-based UI
=====================

Rules implemented (see https://en.boardgamearena.com/gamepanel?game=boop):
  - 6x6 board. Each player starts with 8 Kittens in their supply (0 Cats).
  - On your turn: place one piece (Kitten or Cat) from your supply onto any
    empty cell.
  - The placed piece "boops" (pushes) every adjacent piece one square away,
    in all 8 directions, simultaneously:
      * Cats can boop Kittens and Cats.
      * Kittens can only boop Kittens (never Cats).
      * A boop only happens if the destination square is empty.
      * If a boop would push a piece off the board, it is removed from the
        board and returned to its owner's supply.
      * Only the piece just played does the booping - no chain reactions.
  - After boops resolve, look for 3-in-a-row lines (horizontal, vertical,
    diagonal) belonging to the player who just moved:
      * A line of all Cats -> that player wins immediately.
      * A line of Kittens (or a Kitten/Cat mix) -> the player removes that
        line from the board and gains 3 Cats in their supply. If multiple
        such lines exist, only ONE may be resolved this turn (player picks).
  - If, after playing, all 8 of a player's pieces are on the board:
      * If all 8 are Cats -> that player wins.
      * Otherwise, if that player has no remaining way to ever form a
        Kitten line (no line of 3 cells that's still open/theirs), one of
        their pieces (their choice) is removed from the board and they
        gain a single Cat in their supply instead.

Run this file directly to play a two-player, same-terminal game:
    python boop.py
"""

import sys

SIZE = 6
DIRECTIONS_8 = [(-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)]
LINE_DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]


# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------

def create_board():
    return [[None for _ in range(SIZE)] for _ in range(SIZE)]


def in_bounds(x, y):
    return 0 <= x < SIZE and 0 <= y < SIZE


def make_piece(player, kind):
    return {'player': player, 'kind': kind}  # kind is 'kitten' or 'cat'


def cell_str(cell):
    if cell is None:
        return " ."
    letter = 'K' if cell['kind'] == 'cat' else 'k'
    return f"{letter}{cell['player']}"


def print_board(board):
    header = "    " + "  ".join(f"{i}" for i in range(SIZE))
    print(header)
    for y in range(SIZE):
        row = [cell_str(board[x][y]) for x in range(SIZE)]
        print(f"{y:2}  " + "  ".join(row))
    print()


def print_supply(supply):
    for p in (1, 2):
        s = supply[p]
        print(f"  Player {p} supply: {s['kitten']} kitten(s), {s['cat']} cat(s)")
    print()


def count_on_board(board, player):
    return sum(1 for x in range(SIZE) for y in range(SIZE)
               if board[x][y] and board[x][y]['player'] == player)


def all_cats_on_board(board, player):
    pieces = [board[x][y] for x in range(SIZE) for y in range(SIZE)
              if board[x][y] and board[x][y]['player'] == player]
    return len(pieces) > 0 and all(p['kind'] == 'cat' for p in pieces)


# ---------------------------------------------------------------------------
# Booping
# ---------------------------------------------------------------------------

def can_boop(booper, target):
    if booper['kind'] == 'cat':
        return True
    return target['kind'] == 'kitten'


def resolve_boop(board, x, y, supply):
    """Boop everything adjacent to the piece just placed at (x, y)."""
    booper = board[x][y]
    candidates = []       # (from_x, from_y, to_x, to_y, piece)
    moving_from = set()

    for dx, dy in DIRECTIONS_8:
        fx, fy = x + dx, y + dy
        if not in_bounds(fx, fy):
            continue
        target = board[fx][fy]
        if target is None or not can_boop(booper, target):
            continue
        tx, ty = fx + dx, fy + dy
        candidates.append((fx, fy, tx, ty, target))
        moving_from.add((fx, fy))

    resolved = []
    for fx, fy, tx, ty, piece in candidates:
        if not in_bounds(tx, ty):
            resolved.append((fx, fy, None, piece))          # falls off board
        else:
            occupant = board[tx][ty]
            if occupant is None or (tx, ty) in moving_from:
                resolved.append((fx, fy, (tx, ty), piece))   # can move
            else:
                resolved.append((fx, fy, 'blocked', piece))  # can't move

    # Clear the source cells of everything that actually moves.
    for fx, fy, dest, piece in resolved:
        if dest != 'blocked':
            board[fx][fy] = None

    # Now place pieces at their destinations (or return them to supply).
    for fx, fy, dest, piece in resolved:
        if dest == 'blocked':
            continue
        if dest is None:
            supply[piece['player']][piece['kind']] += 1
            print(f"  -> a {piece['kind']} (Player {piece['player']}) was "
                  f"booped off the board and returned to their supply!")
        else:
            tx, ty = dest
            board[tx][ty] = piece


# ---------------------------------------------------------------------------
# Line detection / graduation
# ---------------------------------------------------------------------------

def find_lines(board, player):
    """All 3-in-a-row lines fully owned by `player` (any mix of kind)."""
    lines = []
    for x in range(SIZE):
        for y in range(SIZE):
            for dx, dy in LINE_DIRECTIONS:
                coords = [(x + dx * i, y + dy * i) for i in range(3)]
                if not all(in_bounds(cx, cy) for cx, cy in coords):
                    continue
                cells = [board[cx][cy] for cx, cy in coords]
                if all(c is not None and c['player'] == player for c in cells):
                    lines.append(coords)
    return lines


def line_all_cats(board, coords):
    return all(board[x][y]['kind'] == 'cat' for x, y in coords)


def graduate_line(board, supply, player, coords):
    for x, y in coords:
        board[x][y] = None
    supply[player]['cat'] += 3


def handle_graduation(board, supply, player):
    """Returns 'win' if a Cat line was found, True if a line was graduated,
    False if there was nothing to do."""
    lines = find_lines(board, player)
    if not lines:
        return False

    cat_lines = [l for l in lines if line_all_cats(board, l)]
    if cat_lines:
        return 'win'

    if len(lines) > 1:
        print(f"Player {player}, you have multiple 3-in-a-row groups. "
              f"Choose which one to graduate into Cats:")
        for i, l in enumerate(lines):
            print(f"  {i + 1}: {l}")
        choice = get_int_input("Choice: ", 1, len(lines)) - 1
        chosen = lines[choice]
    else:
        chosen = lines[0]
        print(f"Player {player} formed a 3-in-a-row! Graduating to Cats.")

    graduate_line(board, supply, player, chosen)
    return True


def can_still_make_kitten_line(board, player):
    """Is there still some 3-cell line with no opposing pieces in it, where
    `player` could in principle end up with 3 Kittens?"""
    for x in range(SIZE):
        for y in range(SIZE):
            for dx, dy in LINE_DIRECTIONS:
                coords = [(x + dx * i, y + dy * i) for i in range(3)]
                if not all(in_bounds(cx, cy) for cx, cy in coords):
                    continue
                cells = [board[cx][cy] for cx, cy in coords]
                blocked = any(
                    c is not None and not (c['player'] == player and c['kind'] == 'kitten')
                    for c in cells
                )
                if not blocked:
                    return True
    return False


def force_convert(board, supply, player):
    print(f"\nPlayer {player}: all 8 of your pieces are on the board and you "
          f"can no longer form a Kitten line.")
    print("Choose one of your pieces to remove from the board; you gain a "
          "Cat in your supply instead.")
    pieces = [(x, y) for x in range(SIZE) for y in range(SIZE)
              if board[x][y] and board[x][y]['player'] == player]
    for i, (x, y) in enumerate(pieces):
        kind = board[x][y]['kind']
        print(f"  {i + 1}: ({x},{y}) - {kind}")
    choice = get_int_input("Choose piece to remove: ", 1, len(pieces)) - 1
    x, y = pieces[choice]
    board[x][y] = None
    supply[player]['cat'] += 1


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def get_int_input(prompt, lo, hi):
    while True:
        raw = input(prompt).strip()
        try:
            v = int(raw)
        except ValueError:
            print(f"Please enter a whole number between {lo} and {hi}.")
            continue
        if lo <= v <= hi:
            return v
        print(f"Please enter a number between {lo} and {hi}.")


def choose_kind(supply, player):
    s = supply[player]
    if s['kitten'] > 0 and s['cat'] > 0:
        while True:
            c = input("Place a (k)itten or (c)at? ").strip().lower()
            if c in ('k', 'kitten'):
                return 'kitten'
            if c in ('c', 'cat'):
                return 'cat'
            print("Please enter 'k' or 'c'.")
    elif s['kitten'] > 0:
        return 'kitten'
    elif s['cat'] > 0:
        return 'cat'
    else:
        raise RuntimeError(f"Player {player} has no pieces left to play - "
                            f"this shouldn't happen.")


def choose_position(board):
    while True:
        raw = input(f"Enter coordinates as 'x y' (each 0-{SIZE - 1}), "
                     f"or 'quit': ").strip()
        if raw.lower() in ('quit', 'exit'):
            print("Thanks for playing!")
            sys.exit(0)
        parts = raw.split()
        if len(parts) != 2:
            print("Please enter two numbers separated by a space, e.g. '2 3'.")
            continue
        try:
            x, y = int(parts[0]), int(parts[1])
        except ValueError:
            print("Coordinates must be integers.")
            continue
        if not in_bounds(x, y):
            print(f"Coordinates must each be between 0 and {SIZE - 1}.")
            continue
        if board[x][y] is not None:
            print("That cell is already occupied. Choose another.")
            continue
        return x, y


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def other_player(p):
    return 2 if p == 1 else 1


def main():
    board = create_board()
    supply = {1: {'kitten': 8, 'cat': 0}, 2: {'kitten': 8, 'cat': 0}}
    current = 1

    print("=" * 40)
    print("Welcome to Boop!")
    print("Legend: k1/K1 = Player 1 kitten/cat, k2/K2 = Player 2 kitten/cat")
    print("=" * 40, "\n")

    while True:
        print_board(board)
        print_supply(supply)
        print(f"--- Player {current}'s turn ---")

        kind = choose_kind(supply, current)
        x, y = choose_position(board)

        board[x][y] = make_piece(current, kind)
        supply[current][kind] -= 1

        resolve_boop(board, x, y, supply)

        result = handle_graduation(board, supply, current)
        if result == 'win':
            print_board(board)
            print(f"*** Player {current} wins with a line of 3 Cats! ***")
            return

        board_count = count_on_board(board, current)
        supply_empty = supply[current]['kitten'] == 0 and supply[current]['cat'] == 0
        if supply_empty and board_count == 8:
            if all_cats_on_board(board, current):
                print_board(board)
                print(f"*** Player {current} wins - all 8 pieces are Cats "
                      f"on the board! ***")
                return
            if not can_still_make_kitten_line(board, current):
                force_convert(board, supply, current)

        current = other_player(current)


if __name__ == "__main__":
    main()