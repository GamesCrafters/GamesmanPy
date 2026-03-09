from models import Game, Value, StringMode
from collections import defaultdict
from typing import Optional

class ChipsChallenge(Game):
    id = 'chipschallenge'
    variants = ["1"]
    n_players = 1
    cyclic = True

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """

        if variant_id not in ChipsChallenge.variants:
            raise ValueError("Variant not defined")
        
        self._variant_id = variant_id
        self.player_piece = "p"
        self.types_of_pieces = "0123456789ABC"
        self.readable_pieces = "cCyYrRbBgGP W"
        self.translation_table = str.maketrans(self.readable_pieces, self.types_of_pieces)
        self.blocking_pieces = "CYRBG"
        self.obtainables = "cyrbgP"
        self.dxdy = [(1,0), (0, 1), (-1, 0), (0,-1)]
        self.key_maps = {(1,0): "d", (0, -1): "w", (-1, 0): "a", (0, 1): "s"}
        self.keybindings = {"d": (1,0), "w": (0, -1),  "a": (-1, 0), "s": (0, 1)}

        match self._variant_id:
            case "1":
                self.row_size = 15
                self.column_size = 14
                self.starting_pos = "  WWWWW WWWWW  " \
                                    "  W   WWW   W  " \
                                    "  W c WPW c W  " \
                                    "WWWWWGWCWGWWWWW" \
                                    "W y B     R y W" \
                                    "W c Wb   rW c W" \
                                    "WWWWWc p cWWWWW" \
                                    "W c Wb   rW c W" \
                                    "W   R  c  B   W" \
                                    "WWWWWWYWYWWWWWW" \
                                    "    W  W  W    " \
                                    "    W cWc W    " \
                                    "    W  Wg W    " \
                                    "    WWWWWWW    "
                self.base = len(set(self.starting_pos)) - 3

    def to_base(self, n, base, readable):
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" if not readable else self.readable_pieces
        
        if n == 0:
            return "0"
        
        result = []
        while n:
            n, r = divmod(n, base)
            result.append(digits[r])
            
        return "".join(reversed(result))
    
    def to_number_string(self, string):
        string = string.replace("p", " ")
        bits = []
        for idx in range(self.row_size*self.column_size):
            if self.starting_pos[idx] not in " W":
                bits.append("0" if string[idx] == " " else "1")
        return "".join(bits)

    def get_item_dict(self, board):
        piece_dict = defaultdict(int)
        start_board = [[self.starting_pos[idx*self.row_size + r] for r in range(self.row_size)] for idx in range(self.column_size)]
        piece_dict["C"] = 1
        for idx_x in range(self.row_size):
            for idx_y in range(self.column_size):
                p = start_board[idx_y][idx_x]
                
                if board[idx_y][idx_x] != p:
                    if p in self.obtainables and p != "c":
                        piece_dict[chr(ord(p)-32)] += 1
                    elif p in self.blocking_pieces and p != "G":
                        piece_dict[p] -= 1
                elif board[idx_y][idx_x] == "c":
                    piece_dict["C"] = 0
        return piece_dict


    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return self.starting_pos
    
    def generate_moves(self, position) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        moves = []
        p = position.find("p")
        player_pos = (p % self.row_size, p // self.row_size)
        board = [[position[idx*self.row_size + r] for r in range(self.row_size)] for idx in range(self.column_size)]
        item_dict = self.get_item_dict(board)
        queue = set([player_pos])
        visited = set()
        while queue:
            curr = queue.pop()
            if curr not in visited:
                visited.add(curr)
                piece = board[curr[1]][curr[0]]
                if piece == "W":
                    continue
                elif piece in self.obtainables:
                    moves.append(curr)
                    continue
                elif piece in self.blocking_pieces:
                    if item_dict[piece] > 0:
                        moves.append(curr)
                    continue
                for dx, dy in self.dxdy:
                    new_x = curr[0] + dx
                    new_y = curr[1] + dy
                    if 0 <= new_x and new_x < self.row_size and 0 <= new_y and new_y < self.column_size:
                        queue.add(tuple([new_x, new_y]))
        return moves
    
    def do_move(self, position, move):
        """
        Returns the resulting position of applying move to position.
        """
        p = position.find("p")
        idx = move[0]+move[1]*self.row_size
        new_pos = position[0:p] + " " + position[p+1::]
        new_pos = new_pos[0:idx] + "p" + new_pos[idx+1::]
        return new_pos

    def primitive(self, position) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        return Value.Win if position.find("P") == -1 else None

    def to_string(self, position, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        if mode == StringMode.Readable:
            board = [position[idx*self.row_size:idx*self.row_size + self.row_size] for idx in range(self.column_size)]
            return "\n".join(board)
        else:
            position = position + (self.column_size*self.row_size - len(position))*" "
            return "1_" + position.replace(' ', '-') 

    def from_string(self, strposition: str):
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """

        return strposition.replace("\n", "")

    def move_to_string(self, move, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        return move
    
    def hash_ext(self, position):
        return int(self.to_number_string(position), base=2)
    
    def generate_single_move(self, position, mode = StringMode.Readable):
        moves = []
        position = position + (self.column_size*self.row_size - len(position))*" "
        p = position.find("p")
        player_pos = (p % self.row_size, p // self.row_size)
        
        board = [[position[idx*self.row_size + r] for r in range(self.row_size)] for idx in range(self.column_size)]

        item_dict = self.get_item_dict(board)
        for dx, dy in self.dxdy:
            new_x = player_pos[0] + dx
            new_y = player_pos[1] + dy
            new_pos = new_x + new_y*self.row_size
            if 0 <= new_x and new_x < self.row_size and 0 <= new_y and new_y < self.column_size:
                piece = position[new_pos]
                if piece in self.obtainables or piece == " ":
                    if mode == StringMode.AUTOGUI:
                        moves.append(f"A_-_{new_pos}_x")
                    else:
                        moves.append(tuple([dx, dy]))
                elif piece in self.blocking_pieces:
                    if item_dict[piece] > 0:
                        if mode == StringMode.AUTOGUI:
                            moves.append(f"A_-_{new_pos}_x")
                        else:
                            moves.append(tuple([dx, dy]))

        if mode == StringMode.AUTOGUI:
            return moves
        
        return [self.key_maps[move] for move in moves]
    
    def resolve_move(self, position, move):
        if type(move) == str and move[0] == "A":
            new_p = int(move.split("_")[2])
            return self.do_move(position, (new_p % self.row_size, new_p // self.row_size))
        else:
            p = position.find("p")
            player_pos = (p % self.row_size, p // self.row_size)
            dx, dy = self.keybindings[move]
            return self.do_move(position, tuple([player_pos[0] + dx, player_pos[1] + dy]))