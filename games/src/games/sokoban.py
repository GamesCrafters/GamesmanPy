from models import Game, Value, StringMode
from typing import Optional
import time
import math

class Sokoban(Game):
    id = 'sokoban'
    variants = ["1", "2", "3", "4", "5", "6", "7", "8"]
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
                
            #"              "
            #roughly 40 billion state space
            case "6":
                self.column_size = 14
                self.row_size = 10
                self.starting_pos = (
                    "############  "
                    "#..  #     ###"
                    "#..  # $  $  #"
                    "#..  #$####  #"
                    "#..    @ ##  #"
                    "#..  # #  $  #"
                    "###### ##$ $ #"
                    "  # $  $ $ $ #"
                    "  #    #     #"
                    "  ############"
                )
            case "7":
                self.column_size = 6
                self.row_size = 7
                self.starting_pos = (
                    "####  "
                    "#@ ###"
                    "# $$.#"
                    "#  $.#"
                    "# $ .#"
                    "# # .#"
                    "######"
                )
            case "8":
                self.column_size = 9
                self.row_size = 9
                self.starting_pos = (
                    " ####### "
                    "##  *  ##"
                    "# .@. . #"
                    "# $ *   #"
                    "#*$$*$$*#"
                    "#   * $ #"
                    "# . . . #"
                    "##  *  ##"
                    " ####### "
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
        
        # O(nm) check
        for y in range(self.row_size):
            for x in range(self.column_size):
                idx = y * self.column_size + x
                if position[idx] in ['$', '*']: 
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
        
        p_idx = self.get_pos_idx(position)
        pos_list[p_idx] = '.' if pos_list[p_idx] == '+' else ' '
        
        bx = box_idx % self.column_size
        by = box_idx // self.column_size
        nx, ny = bx + dx, by + dy 
        n_idx = ny * self.column_size + nx
        
        if pos_list[n_idx] == '.':
            pos_list[n_idx] = '*'
        else:
            pos_list[n_idx] = '$'
            
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
        if position.find('$') == -1:
            return Value.Win
        
        all_boxes = set()
        for i, char in enumerate(position):
            if char in ['$', '*']:
                all_boxes.add(i)

        
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
        Returns a hash using the Combinatorial Number System (Combinadic).
        Generates a dense, collision-free integer for the game state.
        """

        p_idx = self.get_pos_idx(position)
            
        box_indices = [i for i, char in enumerate(position) if char in ['$', '*']]
        
        box_indices.sort(reverse=True)
        
        box_rank = 0
        total_boxes = len(box_indices)
        
        for i, c in enumerate(box_indices):
            k = total_boxes - i  
            box_rank += math.comb(c, k)
            
        max_p_idx = self.column_size * self.row_size 
        
        hash = (box_rank * max_p_idx) + p_idx
        
        return hash

    def move_to_string(self, move: tuple, mode: StringMode) -> str:
        box_idx, dx, dy = move
        direction = self.dirs.get((dx, dy), "?")
        if mode == StringMode.AUTOGUI:
            return f"M_{box_idx}_{box_idx + dx + dy*self.column_size}_y"
        return f"{box_idx}{direction}"

    def to_string(self, position: str, mode: StringMode) -> str:
        
        if mode == StringMode.TUI:
            board = [position[idx * self.column_size : (idx + 1) * self.column_size] for idx in range(self.row_size)]
            return "\n".join(board)
        elif mode == StringMode.Readable:
            return position.replace(' ', 't').replace('#', 'W').replace("@", "p").replace("$", "b").replace("*", "g").replace("+", "P")
        else:
            return "1_" + position.replace(' ', 't').replace('#', 'W').replace("@", "p").replace("$", "b").replace("*", "g").replace("+", "P")

    def from_string(self, strposition: str) -> str:
        clean_pos = strposition.replace('t', ' ').replace('W', '#').replace("p", "@").replace("b", "$").replace("g", "*").replace("P", "+")
        return clean_pos.replace("\n", "").replace("\r", "")
    
    def get_pos_idx(self, position: str):
        p_idx = position.find('@')
        if p_idx == -1:
            p_idx = position.find('+')
        return p_idx; 
