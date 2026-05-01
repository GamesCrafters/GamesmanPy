from models import Game, Value, StringMode
from typing import Optional
from collections import deque
import math

class Sokoban(Game):
    id = 'sokoban'
    variants = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
    n_players = 1
    cyclic = True
    max_spaces = 250 # max number of squares (take max length x width of all levels)
    comb_table = [[math.comb(n, k) for k in range(20)] for n in range(max_spaces)] 

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

        """
        #: wall
        $: box
        .: goal
        @: player
        *: box on goal
        +: player on goal
         : empty
        """

        match self._variant_id:
            # roughly 2,035,800 box arrangements
            # equivalent to Level 1 from the online Sokoban player
            case "1":
                self.column_size = 8
                self.row_size = 9
                self.starting_pos = (
                    "########"
                    "###   ##"
                    "#.@$  ##"
                    "### $.##"
                    "#.##$ ##"
                    "# # . ##"
                    "#$ *$$.#"
                    "#   .  #"
                    "########"
                )

            # roughly 78 box arrangements
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

            # roughly 123,410 box arrangements
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

            # roughly 17,550 box arrangements
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

            # roughly 74,974,368 box arrangements
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

            # roughly 5,985 box arrangements
            case "6":
                self.column_size = 9
                self.row_size = 8
                self.starting_pos = (
                    "  ####   "
                    "  #  #   "
                    "###  ####"
                    "#  +*   #"
                    "# $.. $ #"
                    "### $####"
                    "  #  #   "
                    "  ####   "
                )


            # roughly 2,380 box arrangements
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
            
            # roughly 1,560,780 box arrangements
            case "8":
                self.column_size = 9
                self.row_size = 8
                self.starting_pos = (
                    "   ##### "
                    "####.  ##"
                    "# $.$.  #"
                    "#@$# #$ #"
                    "# $. .  #"
                    "####$#$ #"
                    "  #. .  #"
                    "  #######"
                )

            # roughly 169,911 box arrangements
            case "9":
                self.column_size = 9
                self.row_size = 8
                self.starting_pos = (
                    "   ######"
                    "####.  @#"
                    "#  $$$  #"
                    "#.##.##.#"
                    "#   $   #"
                    "#  $.# ##"
                    "###    # "
                    "  ###### "
                )
            
            # roughly 1,081,575 box arrangements
            case "10":
                self.column_size = 7
                self.row_size = 7
                self.starting_pos = (
                    "#######"
                    "#. . .#"
                    "# $$$ #"
                    "#.$@$.#"
                    "# $$$ #"
                    "#. . .#"
                    "#######"
                )

            # roughly 4,078,044,000 box arrangements
            case "11":
                self.column_size = 11
                self.row_size = 9
                self.starting_pos = (
                    "  #########"
                    "###   #   #"
                    "#  $. * $ #"
                    "# #.#.#.# #"
                    "# $ $@$ $ #"
                    "# #.#.#.# #"
                    "# $ * .$  #"
                    "#   #######"
                    "#####      "
                )

            # roughly 28,754,545,040 box arrangements
            case "12":
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
            
            #roughly 246,463,222,084 box arrangements
            case "13":
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
        self._compute_dead_squares()
           
    def start(self) -> str:
        """Returns the starting position of the game."""
        return self.starting_pos
    
    def generate_moves(self, position: str) -> list[tuple]:
        """
        Returns a list of only the moves that push a box: (box_idx, dx, dy)
        """
        moves = []
        col = self.column_size
        
        p_idx = self.get_pos_idx(position)
        px, py = p_idx % col, p_idx // col
        
        reachable = {(px, py)}
        queue = deque([(px, py)])
        
        while queue:
            curr_x, curr_y = queue.popleft()
            
            for dx, dy in self.dxdy:
                nx, ny = curr_x + dx, curr_y + dy
                if 0 <= nx < col and 0 <= ny < self.row_size:
                    if (nx, ny) not in reachable:
                        n_idx = ny * col + nx
                        if position[n_idx] in {' ', '.', '@', '+'}:
                            reachable.add((nx, ny))
                            queue.append((nx, ny))

        box_indices = []
        idx = position.find('$')
        while idx != -1:
            box_indices.append(idx)
            idx = position.find('$', idx + 1)
            
        idx = position.find('*')
        while idx != -1:
            box_indices.append(idx)
            idx = position.find('*', idx + 1)

        for idx in box_indices:
            x, y = idx % col, idx // col
            
            for dx, dy in self.dxdy:
                player_req_x, player_req_y = x - dx, y - dy
                push_target_x, push_target_y = x + dx, y + dy
                
                if (player_req_x, player_req_y) in reachable:
                    if 0 <= push_target_x < col and 0 <= push_target_y < self.row_size:
                        target_idx = push_target_y * col + push_target_x
                        if position[target_idx] in {' ', '.', '@', '+'}:
                            moves.append((idx, dx, dy))
                                
        return moves

    def do_move(self, position: str, move: tuple) -> str:
        old_box_idx, dx, dy = move
        pos_list = list(position)
        
        old_p_idx = position.find('@')
        if old_p_idx != -1:
            pos_list[old_p_idx] = ' '
        else:
            old_p_idx = position.find('+')
            pos_list[old_p_idx] = '.'
            
        n_idx = old_box_idx + dx + (dy * self.column_size) #new idx of the box
        
        if pos_list[n_idx] == '.':
            pos_list[n_idx] = '*'
        else:
            pos_list[n_idx] = '$'

        #updates the old box idx, which is also the new player idx    
        if position[old_box_idx] == '*': 
            pos_list[old_box_idx] = '+'
        else:
            pos_list[old_box_idx] = '@'
            
        return "".join(pos_list)
    
    def primitive(self, position: str) -> Optional[Value]:
        if position.find('$') == -1:
            return Value.Win

        blocker = {'#', '$', '*'} 
        col = self.column_size

        idx = position.find('$')

        #check to see if any box is surrounded on all 4 sides by a blocker
        while idx != -1:
            
            if idx in self.dead_squares:
                return Value.Loss
                
            if position[idx - 1] in blocker and \
               position[idx - col] in blocker and \
               position[idx - col - 1] in blocker:
                return Value.Loss
                
            if position[idx + 1] in blocker and \
               position[idx - col] in blocker and \
               position[idx - col + 1] in blocker:
                return Value.Loss

            if position[idx - 1] in blocker and \
               position[idx + col] in blocker and \
               position[idx + col - 1] in blocker:
                return Value.Loss
                
            if position[idx + 1] in blocker and \
               position[idx + col] in blocker and \
               position[idx + col + 1] in blocker:
                return Value.Loss

            idx = position.find('$', idx + 1)

        return None


    def hash_ext(self, position: str) -> int:
        """
        Returns a hash using the Combinatorial Number System (Combinadic).
        Generates a dense, collision-free integer for the game state.
        """

        box_indices = []
        
        idx = position.find('$')
        while idx != -1:
            box_indices.append(idx)
            idx = position.find('$', idx + 1)
            
        idx = position.find('*')
        while idx != -1:
            box_indices.append(idx)
            idx = position.find('*', idx + 1)
        
        box_indices.sort(reverse=True)
        
        box_rank = 0
        total_boxes = len(box_indices)
        
        for i, c in enumerate(box_indices):
            k = total_boxes - i  
            box_rank += self.comb_table[c][k]
        
        p_idx = self.get_pos_idx(position)
            
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

    def _compute_dead_squares(self):
        """
        Precomputes all static dead squares using a reverse-pull BFS.
        A square is 'alive' if a box can be theoretically pushed from it to a goal.
        Anything else is a dead square.
        """
        self.dead_squares = set()
        alive_squares = set()
        queue = deque()
        
        col = self.column_size
        row = self.row_size
        
        for y in range(row):
            for x in range(col):
                idx = y * col + x
                if self.starting_pos[idx] in ['.', '+', '*']:
                    alive_squares.add((x, y))
                    queue.append((x, y))
                    
        while queue:
            curr_x, curr_y = queue.popleft()
            
            for dx, dy in self.dxdy:
                prev_x, prev_y = curr_x - dx, curr_y - dy
                
                player_x, player_y = prev_x - dx, prev_y - dy
                
                if (0 <= prev_x < col and 0 <= prev_y < row) and \
                   (0 <= player_x < col and 0 <= player_y < row):
                    
                    prev_idx = prev_y * col + prev_x
                    player_idx = player_y * col + player_x
                    
                    if self.starting_pos[prev_idx] != '#' and self.starting_pos[player_idx] != '#':
                        if (prev_x, prev_y) not in alive_squares:
                            alive_squares.add((prev_x, prev_y))
                            queue.append((prev_x, prev_y))
                            
        for y in range(row):
            for x in range(col):
                idx = y * col + x
                if self.starting_pos[idx] != '#' and (x, y) not in alive_squares:
                    self.dead_squares.add(idx)