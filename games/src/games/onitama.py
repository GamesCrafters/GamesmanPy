from models import Game, Value, StringMode
from typing import Optional
import copy

class CardInfo:
    def __init__(self, moves: int, color: str):
        self.moves = moves
        self.color = color

class OnitamaPosition:
    def __init__(self, red_cards: set[str], blue_cards: set[str], board, neutral_card = None, card_in_queue_for_blue = None, card_in_queue_for_red = None):
        self.active_player = None
        self.red_cards = red_cards
        self.blue_cards = blue_cards
        self.card_in_queue_for_blue = card_in_queue_for_blue
        self.card_in_queue_for_red = card_in_queue_for_red

        self.board = board

        if neutral_card is not None:
            neutral_card_color = Onitama.cards_3x4[neutral_card].color
            if neutral_card_color == 'red':
                self.card_in_queue_for_red = neutral_card
                self.active_player = 'red' 
            else:
                self.card_in_queue_for_blue = neutral_card
                self.active_player = 'blue'

    def __repr__(self):
        board_string = ''
        for row in self.board:
            board_string += str([' ' if item == '' else item for item in row]) + '\n'
        return f"""Active Player: {self.active_player}
                Red Cards: {sorted(list(self.red_cards))}
                Blue Cards: {sorted(list(self.blue_cards))}
                Blue Queued Card: {self.card_in_queue_for_blue}
                Red Queued Card: {self.card_in_queue_for_red}
                ==== Board ====
                {board_string}==============="""

class OnitamaMove:
    def __init__(self, starting_square, ending_square, card_used, player = None, card_slot = None):
        self.starting_square = starting_square
        self.ending_square = ending_square
        self.card_used = card_used
        # which player made the move, and which of their two cards (0 or 1, in sorted order) was used;
        # only needed to build the AutoGUI move string
        self.player = player
        self.card_slot = card_slot

    def __repr__(self):
        col_lut = {0: 'a', 1: 'b', 2: 'c'}
        # Updated for 4 rows
        row_lut = {0: '4', 1: '3', 2: '2', 3: '1'}
        if self.starting_square != self.ending_square:
            return f'{self.card_used[0]}{col_lut[self.starting_square[1]]}{row_lut[self.starting_square[0]]}{col_lut[self.ending_square[1]]}{row_lut[self.ending_square[0]]}'
        else:
            return self.card_used

class Onitama(Game):
    id = 'onitama'
    variants = ["3x4"]
    cards_3x4 = {
        'horse': CardInfo([(0, 1), (-1, 0), (0, -1)], 'red'), # up, left, back
        'goose': CardInfo([(-1, 0), (1, 0), (-1, 1), (1, -1)], 'red'), # sideways, left + up, right + down
        'elephant': CardInfo([(-1, 0), (1, 0), (-1, 1), (1, 1)], 'red'), # sideways, pawn capture
        'mantis': CardInfo([(0, -1), (-1, 1), (1, 1)], 'blue'), # down, pawn capture
        'rat': CardInfo([(0, 1), (-1, 0), (1, 1)], 'blue') # up, left, right + down
    }

    n_players = 2
    cyclic = True
    
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
        board_size = (int(self._variant_id[0]), int(self._variant_id[2]))

        board = [['' for col in range(board_size[0])] for row in range(board_size[1])]
        board[0] = ['P' if col != board_size[0] // 2 else 'M' for col in range(board_size[0])]
        board[-1] = ['p' if col != board_size[0] // 2 else 'm' for col in range(board_size[0])]

        return OnitamaPosition({'horse', 'goose'}, {'mantis', 'rat'}, board, neutral_card='elephant')
    
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
        card_slots = {card: i for i, card in enumerate(sorted(active_player_cards))}

        for card in active_player_cards:
            for move in Onitama.cards_3x4[card].moves:
                board_row_count = len(position.board)
                board_col_count = len(position.board[0])
                for row in range(board_row_count):
                    for col in range(board_col_count):
                        new_row = row - move[1] * (-1 if position.active_player == 'blue' else 1)
                        new_col = col + move[0] * (-1 if position.active_player == 'blue' else 1)
                        if position.board[row][col] in movable_pieces:
                            if new_row >= 0 and new_row < board_row_count and new_col >= 0 and new_col < board_col_count:
                                if position.board[new_row][new_col] not in movable_pieces:
                                    valid_moves.append(OnitamaMove((row, col), (new_row, new_col), card, position.active_player, card_slots[card]))

        # edge case where no move is possible
        if valid_moves == []:
            for card in active_player_cards:
                valid_moves.append(OnitamaMove((0, 0), (0, 0), card, position.active_player, card_slots[card]))

        return valid_moves
    
    def do_move(self, old_position: OnitamaPosition, move: OnitamaMove) -> OnitamaPosition:
        """
        Returns the resulting position of applying move to position.
        """

        # move the piece
        position = copy.deepcopy(old_position)
        piece_moved = position.board[move.starting_square[0]][move.starting_square[1]] 
        position.board[move.starting_square[0]][move.starting_square[1]] = ''
        position.board[move.ending_square[0]][move.ending_square[1]] = piece_moved
        
        # swap the player and rotate cards
        if position.active_player == 'red':
            position.red_cards.remove(move.card_used)
            position.card_in_queue_for_blue = move.card_used
            position.red_cards.add(position.card_in_queue_for_red)
            position.card_in_queue_for_red = None
            position.active_player = 'blue'
        else:
            position.blue_cards.remove(move.card_used)
            position.card_in_queue_for_red = move.card_used
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


    # AutoGUI center layout (must match get_onitama in GamesCraftersUWAPI's image_autogui_data.py):
    #   0-11:   board squares, row-major
    #   12-14:  blue hand left, blue hand right, blue queued card
    #   15-17:  red hand left, red hand right, red queued card
    # A piece move is S_<card center>_M_<from>_<to>_x: the GUI shows the arrow only after the
    # card at <card center> is clicked (selecting a card is not itself a move).
    autogui_blue_slots = 12 # Updated for 3x4 (12 total squares vs 9)
    autogui_red_slots = 15
    # card image characters; red's cards are lowercase, blue's are uppercase (drawn flipped,
    # since blue's moves are rotated 180 degrees on the board)
    autogui_card_chars = {'horse': 'h', 'goose': 'g', 'elephant': 'e', 'mantis': 'n', 'rat': 'r'}

    def to_string(self, position: OnitamaPosition, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        Readable is <active player>_<red cards>_<blue cards>_<queued card>_<board>,
        e.g. r_goose-horse_mantis-rat_elephant_PMP---pmp
        """
        board = ''.join('-' if piece == '' else piece for row in position.board for piece in row)
        if mode == StringMode.Readable:
            queued_card = position.card_in_queue_for_red or position.card_in_queue_for_blue
            return '_'.join([
                position.active_player[0],
                '-'.join(sorted(position.red_cards)),
                '-'.join(sorted(position.blue_cards)),
                queued_card,
                board,
            ])
        elif mode == StringMode.AUTOGUI:
            card_slots = ''
            for hand, queued_card, is_blue in ((position.blue_cards, position.card_in_queue_for_blue, True),
                                               (position.red_cards, position.card_in_queue_for_red, False)):
                for card in sorted(hand) + [queued_card]:
                    if card is None:
                        card_slots += '-'
                    else:
                        char = Onitama.autogui_card_chars[card]
                        card_slots += char.upper() if is_blue else char
            turn = '1' if position.active_player == 'red' else '2'
            return f"{turn}_{board}{card_slots}"
        return repr(position)

    def from_string(self, strposition: str) -> OnitamaPosition:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        active_player, red_cards, blue_cards, queued_card, board_string = strposition.split('_')
        pieces = ['' if char == '-' else char for char in board_string]
        board = [pieces[0:3], pieces[3:6], pieces[6:9], pieces[9:12]]
        pos = OnitamaPosition(set(red_cards.split('-')), set(blue_cards.split('-')), board)
        if active_player == 'r':
            pos.active_player = 'red'
            pos.card_in_queue_for_red = queued_card
        else:
            pos.active_player = 'blue'
            pos.card_in_queue_for_blue = queued_card
        return pos

    def move_to_string(self, move: OnitamaMove, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        if mode == StringMode.AUTOGUI:
            hand_start = Onitama.autogui_red_slots if move.player == 'red' else Onitama.autogui_blue_slots
            if move.starting_square == move.ending_square:
                # no piece can move, so the move is just giving up a card: click that card
                return f"A_-_{hand_start + move.card_slot}_x"
            # the arrow is only shown once the card it uses is selected
            from_square = move.starting_square[0] * 3 + move.starting_square[1]
            to_square = move.ending_square[0] * 3 + move.ending_square[1]
            return f"S_{hand_start + move.card_slot}_M_{from_square}_{to_square}_x"
        return repr(move)

    def hash_ext(self, position: OnitamaPosition) -> int:
        card_list = ['horse', 'goose', 'elephant', 'mantis', 'rat']
        piece_lut = {'': 0, 'p': 1, 'm': 2, 'P': 3, 'M': 4}

        # active player 1 bit
        hash_val = 0 if position.active_player == 'red' else 1
            
        # which card in which hand? 3 * 5 bits
        for card in card_list:
            if card in position.red_cards:
                val = 0
            elif card in position.blue_cards:
                val = 1
            else:
                val = 2
            hash_val = hash_val * 3 + val
                
        # pieces on the board 5 * 12 bits 
        for row in position.board:
            for piece in row:
                hash_val = hash_val * 5 + piece_lut[piece]
                
        return hash_val

    def unhash_ext(self, hash_val: int) -> OnitamaPosition:
        card_list = ['horse', 'goose', 'elephant', 'mantis', 'rat']
        piece_lut = {0: '', 1: 'p', 2: 'm', 3: 'P', 4: 'M'}

        # board
        board_1d = []
        for _ in range(12): # Updated for 12 board tiles
            board_1d.append(piece_lut[hash_val % 5])
            hash_val //= 5
        board_1d.reverse()
        # Reconstruct into 4 rows
        board = [board_1d[0:3], board_1d[3:6], board_1d[6:9], board_1d[9:12]]

        # cards
        red_cards = set()
        blue_cards = set()
        queued_card = None
        
        for card in reversed(card_list):
            val = hash_val % 3
            hash_val //= 3
            if val == 0:
                red_cards.add(card)
            elif val == 1:
                blue_cards.add(card)
            else:
                queued_card = card
                
        active_player = 'red' if (hash_val % 2) == 0 else 'blue'
        
        pos = OnitamaPosition(red_cards, blue_cards, board)

        pos.active_player = active_player
        # card in queue is for active player
        if active_player == 'red':
            pos.card_in_queue_for_red = queued_card
            pos.card_in_queue_for_blue = None
        else:
            pos.card_in_queue_for_blue = queued_card
            pos.card_in_queue_for_red = None
            
        return pos
    