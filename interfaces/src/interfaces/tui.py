from solver import AcyclicSolver
from database import GameDB
from games import getGame
from models import Game, StringMode, Value

class TUI:
    def __init__(self):
        pass

    def play(self, game: Game, variant: str):
        print(game)
        db = GameDB(game.id, variant)
        curr_pos = game.start()
        while game.primitive(curr_pos) is None:
            print("current position:")
            self.print_position(game, curr_pos)
            moves = game.generate_moves(curr_pos)
            curr_val = db.get(curr_pos)
            print(f'Position is a {"win" if curr_val[1] == Value.Win else "lose"} in {curr_val[0]} moves.')
            for move in moves:
                possible = game.do_move(curr_pos, move)
                val = db.get(possible)
                print(f'{move}: {"Winning Move" if val[1] == Value.Loss else "Losing Move"} in {val[0]}')
            user_move_index = int(input("choose a move")) - 1
            user_move = moves[user_move_index]
            curr_pos = game.do_move(curr_pos, user_move)
        print("GAME OVER")

    def print_position(self, game: Game, position: int):
        print(game.to_string(position, StringMode.Readable))