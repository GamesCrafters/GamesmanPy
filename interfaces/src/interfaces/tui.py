from solver import Solver
from database import SqliteDB
from games import get_game, game_list
from models import *
from typing import Optional

class TUI:
    def __init__(self):
        (self._game, self.variant) = self.select_game()
        self.game = self._game(self.variant)
        self.play(self.game, self.variant)


    def play(self, game: Game, variant: str):
        import sqlite3
        use_db = True
        db = None
        try:
            db = SqliteDB(game.id, variant)
            _ = db.get(game.start())
        except sqlite3.OperationalError:
            use_db = False
            print("(No solver database for this game — playing without win/loss hints.)")
        curr_pos = game.start()
        while game.primitive(curr_pos) is None:
            print("Current position:")
            self.print_position(game, curr_pos)
            moves = game.generate_moves(curr_pos)
            hashed = self.game.hash_ext(curr_pos)
            (curr_rem, curr_val) = db.get(hashed)
            print(f'Position is a {self.get_value_str(curr_val)} in {curr_rem} moves.')
            moves_map = {self.get_move_string(game, move): move for move in moves}
            for move in moves_map.keys():
                possible = game.do_move(curr_pos, moves_map[move])
                hashed_child = self.game.hash_ext(possible)
                (rem, val) = db.get(hashed_child)
                move_val = self.get_move_value(val)
                print(f'{move}: {self.get_value_str(move_val)} in {rem}')
            user_move = self.get_valid_move(moves_map.keys())
            curr_pos = game.do_move(curr_pos, moves_map[user_move])
        self.print_position(game, curr_pos)
        result = game.primitive(curr_pos)
        print("GAME OVER" + (" — You win!" if result == Value.Win else " — No solution."))
        if hasattr(game, "get_exit_counts_display"):
            msg = game.get_exit_counts_display(curr_pos)
            if msg:
                print(msg)

    def get_move_value(self, child_val):
        if self.game.n_players == 1:
            return child_val
        if child_val == Value.Loss:
            return Value.Win
        if child_val == Value.Tie:
            return Value.Tie
        if child_val == Value.Win:
            return Value.Loss
        return Value.Draw
    
    def get_value_str(self, val):
        match val:
            case Value.Win: return "win"
            case Value.Loss: return "loss"
            case Value.Tie: return "tie"
            case Value.Draw: return "draw"

    def print_position(self, game: Game, position: int):
        print(game.to_string(position, StringMode.TUI))
    
    def get_move_string(self, game: Game, move: int):
        return game.move_to_string(move, StringMode.TUI)
    
    def get_valid_move(self, moves: list[str]) -> str:
        moves = list(moves)
        lower_map = {move.lower(): move for move in moves}
        user_input = input("Select a move: ")
        if user_input == 'q':
            exit()
        while user_input not in moves and user_input.lower() not in lower_map:
            user_input = input("Invalid move. Please select a valid move: ")
            if user_input == 'q':
                exit()
        if user_input in moves:
            return user_input
        return lower_map[user_input.lower()]
    
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
