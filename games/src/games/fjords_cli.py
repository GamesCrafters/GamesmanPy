"""
Interactive terminal loop for playing Fjords against a random-move
opponent. Not part of the GamesmanPy Game contract -- just a way to play
the game before the full solver/TUI-string pipeline is built out.

Run from the repo root:
    python3 games/src/games/fjords_cli.py
"""
import os
import random
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GAMES_SRC = os.path.dirname(_THIS_DIR)  # .../games/src
_REPO_ROOT = os.path.dirname(os.path.dirname(_GAMES_SRC))  # repo root
_MODELS_SRC = os.path.join(_REPO_ROOT, "models", "src")
for _path in (_MODELS_SRC, _GAMES_SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from games.fjords import Fjords  # noqa: E402
from models import StringMode  # noqa: E402


def prompt_for_move(game: Fjords, position: int, legal_moves: list[int]) -> int:
    legal_vertices = sorted(game._mutable_indices[m] for m in legal_moves)
    print(f"Legal vertices: {legal_vertices}")
    while True:
        raw = input("Pick a vertex to color: ").strip()
        if not raw.isdigit():
            print("Please enter a vertex number.")
            continue
        vertex = int(raw)
        move = game._board_index_to_digit.get(vertex)
        if move is None or move not in legal_moves:
            print("That's not a legal move right now.")
            continue
        return move


def main() -> None:
    game = Fjords("regular")
    position = game.start()
    human_color = game._BLUE

    while True:
        print()
        print(game.to_string(position, StringMode.TUI))

        value = game.primitive(position)
        if value is not None:
            digits = game._unpack(position)
            loser = game._turn_code(digits)
            loser_name = "Blue" if loser == game._BLUE else "Red"
            winner_name = "Red" if loser == game._BLUE else "Blue"
            print(f"\n{loser_name} has no legal move. {winner_name} wins!")
            break

        digits = game._unpack(position)
        turn = game._turn_code(digits)
        legal_moves = game.generate_moves(position)

        if turn == human_color:
            print("Blue's turn (you).")
            move = prompt_for_move(game, position, legal_moves)
            position = game.do_move(position, move)
        else:
            move = random.choice(legal_moves)
            vertex = game._mutable_indices[move]
            print(f"Red's turn (computer) -> plays vertex {vertex}.")
            position = game.do_move(position, move)


if __name__ == "__main__":
    main()
