from games.ten_to_zero import TenToZero
from models import Game
from typing import Optional

game_list = {
    "ten-to-zero": TenToZero,
}

def getGame(game_id: str, variant_id: str) -> Optional[Game]:
    game = game_list.get(game_id)
    if game is None or variant_id not in game.variants:
        return None
    return game
    