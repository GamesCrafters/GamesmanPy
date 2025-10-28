from solver import AcyclicSolver
from database import GameDB
from games import get_game, game_list
from models import *
from typing import Optional

class TUI:
    def __init__(self):
        (self.game, self.variant) = self.select_game()
        self.play(self.game, self.variant)


    def play(self, game: Game, variant: str):
        db = GameDB(game.id, variant)
        curr_pos = game.start()
        while game.primitive(curr_pos) is None:
            print("Current position:")
            self.print_position(game, curr_pos)
            moves = game.generate_moves(curr_pos)
            curr_val = db.get(curr_pos)
            print(f'Position is a {"win" if curr_val[1] == Value.Win else "lose"} in {curr_val[0]} moves.')
            moves_map = {self.get_move_string(game, move): move for move in moves}
            for move in moves_map.keys():
                possible = game.do_move(curr_pos, moves_map[move])
                val = db.get(possible)
                print(f'{move}: {"Winning Move" if val[1] == Value.Loss else "Losing Move"} in {val[0]}')
            user_move = self.get_valid_move(moves_map.keys())
            curr_pos = game.do_move(curr_pos, moves_map[user_move])
        self.print_position(game, curr_pos)
        print("GAME OVER")

    def print_position(self, game: Game, position: int):
        print(game.to_string(position, StringMode.Readable))
    
    def get_move_string(self, game: Game, move: int):
        return game.move_to_string(move, StringMode.Readable)
    
    def get_valid_move(self, moves: list[str]) -> str:
        user_input = input("Select a move: ")
        if user_input == 'q':
            exit()
        while user_input not in moves:
            user_input = input("Invalid move. Please select a valid move: ")
            if user_input == 'q':
                exit()
        return user_input
    
    def select_game(self) -> Game:
        print(f'Games: {', '.join(game_list.keys())}')
        game_id = input("Enter Game ID: ")
        variant_id = input("Enter Variant ID: ")
        game_res = get_game(game_id, variant_id)
        while game_res.is_err():
            print(game_res.unwrap_err())
            game_id = input("Enter Game ID: ")
            variant_id = input("Enter Variant ID: ")
            game_res = get_game(game_id, variant_id)
        return (game_res.unwrap(), variant_id)