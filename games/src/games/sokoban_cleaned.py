from models import Game, Value, StringMode
from typing import Optional

class Sokoban(Game):
    id = 'sokoban'
    variants = ["1", "2", "3", "4", "5"]
    n_players = 1
    cyclic = True 

    def __init__(self, variant_id: str):
        """
        Define instance variables and the starting board.
        """
        if variant_id not in Sokoban.variants:
            raise ValueError("Variant not defined")
        
        self._variant_id = variant_id
        
        # Directions: Right, Down, Left, Up
        self.dxdy = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.dirs = {(1, 0): "R", (0, 1): "D", (-1, 0): "L", (0, -1): "U"}

        match self._variant_id:
            case "1": # equivalent to Level 1 from the online Sokoban player
                self.column_size = 6
                self.row_size = 7
                self.starting_pos = (
                    "##   #"
                    ".@$  #"
                    "## $.#"
                    ".##$ #"
                    " # . #"
                    "$ *$$."
                    "   .  "
                )
            case "2":
                self.column_size = 8
                self.row_size = 8
                self.starting_pos = (
                    "  ###   "
                    "  # #   "
                    "  #.#   "
                    "###$#   "
                    "#. $@###"
                    "####   #"
                    "   #   #"
                    "   #####"
                )

            case "3":
                self.column_size = 11
                self.row_size = 10
                self.starting_pos = (
                    "########## "
                    "#        # "
                    "# $$ $   # "
                    "#      ### "
                    "####   #   "
                    "   # @ #   "
                    "   # $ #   "
                    "####   ####"
                    "#....     #"
                    "###########"
                )
            case "4":
                self.column_size = 9
                self.row_size = 9
                self.starting_pos = (
                    "  #####  "
                    "  #   #  "
                    "###$  #  "
                    "#   $ #  "
                    "#   @ ###"
                    "##### $ #"
                    "  ### $ #"
                    "  #.... #"
                    "  #######"
                )
            #"                      "
            case "5":
                self.column_size = 23
                self.row_size = 12
                self.starting_pos = (
                    "    #####              "
                    "    #   #              "
                    "    #$  #              "
                    "  ###  $###            "
                    "  #  $  $ #            "
                    "### # ### #            "
                    "#   # ### #      ######"
                    "#   # ### ########  ..#"
                    "# $  $              ..#"
                    "##### ####  #@####  ..#"
                    "    #       ###  ######"
                    "    #########          "
                )
           
    def start(self) -> str:
        """Returns the starting position of the game."""
        return self.starting_pos
    
    def generate_moves(self, position: str) -> list[tuple]:
        """
        Returns a list of only the moves that push a box: (box_idx, dx, dy)
        
        """
        moves = []
        
        p_idx = self.get_pos_idx(position)
            
        px, py = p_idx % self.column_size, p_idx // self.column_size
        
        # 1. BFS to find all spaces the player can currently reach
        reachable = set()
        queue = [(px, py)]
        
        while queue:
            curr_x, curr_y = queue.pop(0)
            if (curr_x, curr_y) not in reachable:
                reachable.add((curr_x, curr_y))
                
                for dx, dy in self.dxdy:
                    nx, ny = curr_x + dx, curr_y + dy
                    if 0 <= nx < self.column_size and 0 <= ny < self.row_size:
                        n_idx = ny * self.column_size + nx
                        if position[n_idx] in [' ', '.']:
                            queue.append((nx, ny))
        
        # 2. Check all boxes to see if they can be pushed
        for y in range(self.row_size):
            for x in range(self.column_size):
                idx = y * self.column_size + x
                if position[idx] in ['$', '*']: # Found a box
                    for dx, dy in self.dxdy:
                        player_req_x, player_req_y = x - dx, y - dy
                        push_target_x, push_target_y = x + dx, y + dy
                        
                        if (player_req_x, player_req_y) in reachable:
                            if 0 <= push_target_x < self.column_size and 0 <= push_target_y < self.row_size:
                                target_idx = push_target_y * self.column_size + push_target_x
                                if position[target_idx] in [' ', '.', '@', '+']:
                                    moves.append((idx, dx, dy))
        return moves

    def do_move(self, position: str, move: tuple) -> str:
        box_idx, dx, dy = move
        pos_list = list(position)
        
        # 1. Remove player from old position
        p_idx = self.get_pos_idx(position)
        pos_list[p_idx] = '.' if pos_list[p_idx] == '+' else ' '
        
        # 2. Calculate new coordinates for the pushed box
        bx = box_idx % self.column_size
        by = box_idx // self.column_size
        nx, ny = bx + dx, by + dy 
        n_idx = ny * self.column_size + nx
        
        # 3. Place the box in its new location
        if pos_list[n_idx] == '.':
            pos_list[n_idx] = '*'
        else:
            pos_list[n_idx] = '$'
            
        # 4. Move the player into the tile the box just vacated
        if position[box_idx] == '*': 
            pos_list[box_idx] = '+'
        else:
            pos_list[box_idx] = '@'
            
        return "".join(pos_list)

    def primitive(self, position: str) -> Optional[Value]:
        """
        Returns Value.Win if all boxes are on goals.
        Returns Value.Lose if any box is deadlocked in a corner.
        Otherwise returns None.
        """
        # 1. Win Condition
        if position.find('$') == -1:
            return Value.Win

        # 2. Corner Deadlock Detection
        for y in range(self.row_size):
            for x in range(self.column_size):
                idx = y * self.column_size + x
                if position[idx] == '$':
                    up = (y == 0) or (position[(y - 1) * self.column_size + x] == '#')
                    down = (y == self.row_size - 1) or (position[(y + 1) * self.column_size + x] == '#')
                    left = (x == 0) or (position[y * self.column_size + (x - 1)] == '#')
                    right = (x == self.column_size - 1) or (position[y * self.column_size + (x + 1)] == '#')

                    if (up or down) and (left or right):
                        return Value.Loss

        return None

    def hash_ext(self, position: str) -> int:
        """
        Returns a perfect hash using bitpacking.
        Only dynamic elements (Player and Boxes) are stored.
        """
        # 1. Find the player's index
        p_idx = self.get_pos_idx(position)
            
        # 2. Find all box indices ('$' for floor, '*' for goal)
        box_indices = []
        for i, char in enumerate(position):
            if char in ['$', '*']:
                box_indices.append(i)
                
        # 3. Sort the boxes
        box_indices.sort()
        
        # 4. Calculate how many bits we need per index
        # For an 8x8 board (64 tiles, max index 63), this returns 6 bits.
        max_index = self.column_size * self.row_size - 1
        bits_per_index = max_index.bit_length() 
        
        packed_hash = p_idx
        
        for b_idx in box_indices:
            packed_hash = (packed_hash << bits_per_index) | b_idx
            
        return packed_hash

    def move_to_string(self, move: tuple, mode: StringMode) -> str:
        box_idx, dx, dy = move
        direction = self.dirs.get((dx, dy), "?")
        return f"{box_idx}{direction}"

    def to_string(self, position: str, mode: StringMode) -> str:
        if mode in [StringMode.Readable, StringMode.TUI]:
            board = [position[idx * self.column_size : (idx + 1) * self.column_size] for idx in range(self.row_size)]
            return "\n".join(board)
        else:
            return f"{self._variant_id}_" + position.replace(' ', '-') 

    def from_string(self, strposition: str) -> str:
        return strposition.replace("\n", "")
    
    #helper functions
    def get_pos_idx(self, position: str):
        p_idx = position.find('@')
        if p_idx == -1:
            p_idx = position.find('+')
        return p_idx; 