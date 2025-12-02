from .solver import Solver
from games import game_list, get_game
from models import *
import argparse

parser = argparse.ArgumentParser(description="GamesmanPy Solver cli")

parser.add_argument("game_id", help="Game ID", nargs="?", default=None)
parser.add_argument("-v", "--variant", help="Variant ID", type=str, default=None)
parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing db?")
args = parser.parse_args()

game_id = args.game_id
overwrite = args.overwrite
variant_id = args.variant


def main():
    if game_id is None:
        for game in game_list.values():
            s = Solver(game)
            s.solve(overwrite)
    else:
        game = get_game(game_id) if variant_id is None else get_game(game_id, variant_id)
        match game:
            case Ok(value): game = value
            case Err(error):
                print(error)
                exit()
        s = Solver(game)
        s.solve(overwrite=overwrite, variant=variant_id)