from ten_to_zero import TenToZero
from models.game import Game
from typing import Optional

games = {
    "ten-to-zero": TenToZero,
}

def getGame(game_id: str, variant_id: str) -> Optional[Game]:
    game = games.get(game_id)
    if game is None:
        return None
    return game(variant_id)
    