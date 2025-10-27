from .ten_to_zero import TenToZero
from .ttt_inf import TTT_inf
from models import Game
from typing import Optional
from models import Result

game_list = {
    "ten-to-zero": TenToZero,
    "ttt-inf": TTT_inf,
}

def getGame(game_id: str, variant_id: str) -> Optional[Game]:
    game = game_list.get(game_id)
    if game is None:
        return Result.err("Game not found")
    if variant_id not in game.variants:
        return Result.err("Variant not found")
    return Result.ok(game)
    