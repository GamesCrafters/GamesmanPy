from .ten_to_zero import TenToZero
from .ttt_inf import TTT_inf
from models import *

game_list = {
    "ten-to-zero": TenToZero,
    "ttt-inf": TTT_inf,
}

def validate(game_id: str, variant_id: str) -> bool:
    game = game_list.get(game_id)
    return game is not None and variant_id in game.variants

def get_game(game_id: str, variant_id: str) -> Result[Game, str]:
    game = game_list.get(game_id)
    if game is None:
        return Err("Invalid game ID")
    if variant_id not in game.variants:
        return Err("Invalid variant ID")
    return Ok(game)
    