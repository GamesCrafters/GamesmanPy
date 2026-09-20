from models import Game, Value, StringMode
from typing import Optional

"""Position: [if player 1's turn, add 1 to the start; if Player 0, it is implicitly 0] + 19 tiles [what player is occupying] 1 if empty, 2 if white, 3 if black
Move: [move]n - 06, 0710, 0713, 0718, 08, 071114, 071114"""

class Bug(Game):
    id = 'bug'
    variants = ["regular"]
    n_players = 2
    cyclic = False

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Test.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        pass

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return 1
    
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        # First, eat all the bugs
        # Second, return a list of available placement (1, ji)
        origin = [0,0,0]
        board = Board(position)
        player = board.player
        if position == 1:
            return [2, 3]
        elif position == 2:
            return [4, 5]
        elif position == 4:
            return [2]
        return []
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        # you get a position like 101201201201201201200000 (20 digits, first digit is player turn indicator)
        # 130132 <- means change 34 to 1, which is white, change 12 to black
        #if no moves left, return 10 for white win, or 20 for black win

        # MANLIN'S PART FEEL FREE TO DELETE
        # assume we get a 334455 etc. as placements for the current player type.
        # NEED TO HAVE A FUNCTION THAT UNPACKS THE ABOVE INTO THE MORE DETAILED MOVE AS DESCRIBED 3 LINES UP

        player_turn = 0 if len(str(position)) == 19 or 1 else len(str(position)) == 1

        pos_str = str(position)
        pos_str_clean = pos_str[1:] if player_turn == 1 else pos_str[:] #remove player info because we don't need it for now
        tilenum_to_chari = {'11':0, '12':2, '13':4} #etc finish this out cbb / this converts the 3:3 gui format to the actual index position in the pos_string

        triplets = [pos_str[i : i + 3] for i in range(0, len(pos_str), 3)]
        changes_in_order = {tile[1] + tile[2] : tile[0] for tile in triplets}

        #iterate through the list of needed changes and apply them to the position string, allowing for multiple updates to the same tile
        for tile in changes_in_order:
            #if at very end, want to avoid indexing error
            if tile == "44":
                pos_str_clean= pos_str_clean[:tilenum_to_chari[tile]] + changes_in_order[tile]
            else:
                pos_str_clean = pos_str_clean[:tilenum_to_chari[tile]] + changes_in_order[tile] + pos_str_clean[tilenum_to_chari[tile] + 1:]


        #swap player turn
        updated_pos_string = str(abs(player_turn - 1)) + pos_str_clean
        
        return int(updated_pos_string)

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        if position == 10 or position == 20:
            return Value.Win
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        return str(position)

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        return int(strposition)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        
        return str(move)



    class Board:
            def __init__(self, position):
                self.lst = [[[None for _ in range(5)] for _ in range(5)] for _ in range(5)]
                for i in range(5):
                    for j in range(5):
                        for k in range(5):
                            if abs((i -2) + (j - 2) + (k - 2)) > 2:
                                pass
                            self.lst[i][j][k] = position % 10
                            position //= 10
                self.player = position
                
                
            def setitem (self, index, value):
                self.lst[index[0]-2][index[1]-2][index[2]-2] = value

            def getitem(self, index):
                return self.lst[index[0]-2][index[1]-2][index[2]-2]

            def neighbors(self, index):
                i = index[0]
                j = index[1]
                k = index[2]
                neighbors = []
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        for dk in [-1, 0, 1]:
                            if abs(di) + abs(dj) + abs(dk) == 1:
                                ni, nj, nk = i + di, j + dj, k + dk
                                if 0 <= ni < 5 and 0 <= nj < 5 and 0 <= nk < 5:
                                    neighbors.append((ni, nj, nk))
                return neighbors

    class Group:
        def __init__(self, index, board, bugs):
            self.indexes = [index]
            self.board = board
            self.color = board.getitem(index)
            self.size = 1
            self.shape = ['', '', '']
            self.bugs = bugs

        def expand(self):
            new_indexes = []
            for index in self.indexes:
                for neighbor in self.board.neighbors(index):
                    if self.board.getitem(neighbor) == self.color and neighbor not in self.indexes and neighbor not in new_indexes:
                        new_indexes.append(neighbor)
                        if neighbor[0] < self.shape[0]:
                            self.shape[0].append('-i')
                        if neighbor[0] > self.shape[0]:
                            self.shape[0].append('+i')
                        if neighbor[1] < self.shape[1]:
                            self.shape[1].append('-j')
                        if neighbor[1] > self.shape[1]:
                            self.shape[1].append('+j')
                        if neighbor[2] < self.shape[2]:
                            self.shape[2].append('-k')
                        if neighbor[2] > self.shape[2]:
                            self.shape[2].append('+k')
            self.indexes.extend(new_indexes)
            self.size = len(self.indexes)
            if new_indexes:
                self.expand()

            def disassemble(self):
                for index in self.indexes:
                    self.board.setitem(index, 0)

            def same_shape(self, bug):
                axes = "ijk"
                def parse(term):
                    signs, sign = [], 1
                    for ch in "".join(str(term).split()):
                        if ch == "+":
                            sign = 1
                        elif ch == "-":
                            sign = -1
                        elif ch in axes:
                            signs.append(sign)
                        return tuple(signs)

                def flip(slot):
                    return tuple(-s for s in slot)

                target = [parse(t) for t in bug.shape]
                shape = [parse(t) for t in self.shape]

                for _ in range(6):
                    if shape == target:
                        return True
                    shape = [flip(shape[2]), shape[0], shape[1]]

                return False

            def try_eat(self):
                gone = []
                moves = [[],[],[],[],[],[]]
                for index in self.indexes:
                    for neighbor in self.board.neighbors(index):
                        if self.board.getitem(neighbor) != self.color and self.board.getitem(neighbor) != 0:
                            for bug in self.bugs:
                                if neighbor in bug.indexes and bug.color != self.color and bug.size < self.size and self.same_shape(bug):
                                    gone.append(bug)
                i = 0
                for bug in gone:
                    for bug_index in bug.indexes:
                        for point in self.board.neighbors(bug_index):
                            if self.board.getitem(point) == 0 or point in bug.indexes:
                                moves[bug_index[i]].append(point)
                    i += 1
                return moves

    