from models import Game, Value, StringMode
from typing import Optional

class CardInfo:
    def __init__(self, moves: int, color: str):
        self.moves = moves
        self.color = color

class OnitamaMove:
    def __init__(self, starting_square, ending_square, card_used):
        self.starting_square = starting_square
        self.ending_square = ending_square
        self.card_used = card_used

    def __repr__(self):
        return f'{self.starting_square} to {self.ending_square} using {self.card_used}'
    
class OnitamaPosition:
    def __init__(self,
                 board_x_length: int, board: str,
                 red_cards: tuple[str], blue_cards: tuple[str], 
                 card_in_queue_for_blue = None, card_in_queue_for_red = None, 
                 ):
        
        self.board_x_length = board_x_length
        self.board = board

        self.red_cards = red_cards
        self.blue_cards = blue_cards

        self.card_in_queue_for_blue = card_in_queue_for_blue
        self.card_in_queue_for_red = card_in_queue_for_red

        if card_in_queue_for_red != None:
            self.active_player = 'red'
        else:
            self.active_player = 'blue'

    def __repr__(self):
        return f'{self.active_player}/{self.red_cards}/{self.blue_cards}/{self.card_in_queue_for_blue}/{self.card_in_queue_for_red}/{self.board}'

class Onitama(Game):
    id = 'onitama'
    variants = ["3x4"]
    n_players = 2
    cyclic = True

    cards_3x4 = {
        'dog': CardInfo((6), 'red'), # forward 2 squares
        'lobster': CardInfo((-3), 'red'), # backward 1 square
        'frog': CardInfo((4, 2), 'red'), # moves like pawn captures
        'toad': CardInfo((-4, -2), 'blue'), # moves like pawn captures in reverse
        'crab': CardInfo((-1, 1), 'blue') # moves 1 square sideways
    }

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Onitama.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id

    def start(self) -> str:
        """
        Returns the starting position of the game.
        """
        variant = self._variant_id

        # TODO: Implement varying board sizes for different variants
        num_rows = variant[3]
        num_cols = variant[0]

        blue_home_row = 'PMP'
        empty_row = 'ooo'
        red_home_row = 'pmp'
        
        return OnitamaPosition(blue_home_row + empty_row + empty_row + red_home_row,
                               {'dog', 'lobster'}, {'toad', 'crab'}, card_in_queue_for_red= 'frog')

    def generate_single_move(self, move, position):
        
        new_row = row + move[1]
        new_col = col + move[0]
        if position.board[row][col] in movable_pieces:
            if new_row >= 0 and new_row < board_row_count and new_col >= 0 and new_col < board_col_count:
                if position.board[new_row][new_col] not in movable_pieces:
                    valid_moves.append(OnitamaMove((row, col), (new_row, new_col), card))
    
    def generate_moves(self, position: OnitamaPosition) -> list[OnitamaMove]:
        """
        Returns a list of positions given the input position.
        """
        valid_moves = []

        if position.active_player == 'red':
            movable_pieces = {'p', 'm'}
            active_player_cards = position.red_cards
        else:
            movable_pieces = {'P', 'M'}
            active_player_cards = position.blue_cards

        for card in active_player_cards:
            for move in Onitama.cards_3x4[card].moves:
                onitama_move = self.generate_single_move(move, moveable_pieces, position)
                if onitama_move != None:
                    valid_moves.append(onitama_move)

        return valid_moves
    
    def do_move(self, position: OnitamaPosition, move: OnitamaMove) -> OnitamaPosition:
        """
        Returns the resulting position of applying move to position.
        """

        # TODO: make this mutable

        # move the piece
        position.board[move.ending_square[0]][move.ending_square[1]] = position.board[move.starting_square[0]][move.starting_square[1]] 
        position.board[move.starting_square[0]][move.starting_square[1]] = ''
        
        # swap the player and rotate cards
        if position.active_player == 'red':
            position.card_in_queue_for_blue = position.red_cards.remove(move.card_used)
            position.red_cards.add(position.card_in_queue_for_red)
            position.card_in_queue_for_red = None
            position.active_player = 'blue'
        else:
            position.card_in_queue_for_red = position.blue_cards.remove(move.card_used)
            position.blue_cards.add(position.card_in_queue_for_blue)
            position.card_in_queue_for_blue = None
            position.active_player = 'red'

        return position

    def primitive(self, position: OnitamaPosition) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        red_master_alive = False
        blue_master_alive = False
        red_master_in_temple = False
        blue_master_in_temple = False

        board_row_count = len(position.board)
        board_col_count = len(position.board[0])
    
        for i, row in enumerate(position.board):
            for j, piece in enumerate(row):

                if piece == 'm':
                    red_master_alive = True
                    if i == 0 and j == board_col_count // 2:
                        red_master_in_temple = True
                elif piece == 'M':
                    blue_master_alive = True
                    if i == board_row_count - 1 and j == board_col_count // 2:
                        blue_master_in_temple = True

        if position.active_player == 'red':
            if blue_master_in_temple:
                return Value.Loss
            elif not red_master_alive:
                return Value.Loss
            elif not blue_master_alive:
                return Value.Win
            elif red_master_in_temple:
                return Value.Win
        else:
            if not blue_master_alive:
                return Value.Loss
            elif red_master_in_temple:
                return Value.Loss
            elif blue_master_in_temple:
                return Value.Win
            elif not red_master_alive:
                return Value.Win


    def to_string(self, position: OnitamaPosition, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        return repr(position)

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        pass

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        pass

o = Onitama("3x4")
starting_position = o.start()
moves = o.generate_moves(starting_position)
print(moves)
new_pos = o.do_move(starting_position, moves[0])
print(new_pos.board)
print(o.primitive(new_pos))
print(new_pos)