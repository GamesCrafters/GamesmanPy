from .clobber import Clobber
from .horses import Horses
from .pancakes import Pancakes
from .snakestale import Snakestale
from .chipschallenge import ChipsChallenge
from .test import Test
from models import *

game_list = {
    "chipschallenge": ChipsChallenge,
    "clobber": Clobber,
    "horses": Horses,
    "pancakes": Pancakes,
    "snakestale": Snakestale,
    "test": Test,
}

def validate(game_id: str, variant_id: str) -> bool:
    game = game_list.get(game_id)
    return game is not None and variant_id in game.variants

def get_game(game_id: str, variant_id: str=None) -> Result[Game, str]:
    game = game_list.get(game_id)
    if game is None:
        return Err("Invalid game ID")
    if variant_id is not None and variant_id not in game.variants:
        return Err("Invalid variant ID")
    return Ok(game)
    