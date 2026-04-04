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
        # O(nm) check
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
        
        all_boxes = set()
        for i, char in enumerate(position):
            if char in ['$', '*']:
                all_boxes.add(i)

        
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


        # while loop should only run a maximum of B times
        # where B is the number of boxes in the position
        # can not call generate moves --> messes with autogui
        # also, just a really slow bfs call in general
        """
        while True:
            moves = self.generate_moves(current_position)
            new_live_boxes = set(move[0] for move in moves)

            if not new_live_boxes:
                break
                
            live_boxes.update(new_live_boxes)

            pos_list = list(position)
            for idx in live_boxes:
                if pos_list[idx] == '$':
                    pos_list[idx] = ' '
                elif pos_list[idx] == '*':
                    pos_list[idx] = '.'

            current_position = "".join(pos_list)
            
        
        dead_boxes = all_boxes - live_boxes

        for idx in dead_boxes:
            # If a Dead Box is NOT on a goal square ('*'), the state is lost
            if position[idx] != '*':
                return Value.Loss
        """

        return None


    def hash_ext(self, position: str) -> int:
        """
        Returns a hash using the Combinatorial Number System (Combinadic).
        Generates a dense, collision-free integer for the game state.
        """

        p_idx = self.get_pos_idx(position)
            
        #optimize this further by maybe storing this?
        box_indices = [i for i, char in enumerate(position) if char in ['$', '*']]
        
        box_indices.sort(reverse=True)
        
        box_rank = 0
        total_boxes = len(box_indices)
        
        for i, c in enumerate(box_indices):
            k = total_boxes - i  
            box_rank += math.comb(c, k)
            
        # prevent overlap from player index by getting max int
        max_p_idx = self.column_size * self.row_size 
        
        hash = (box_rank * max_p_idx) + p_idx
        
        return hash
    
        """
    #optimize hash because this is not going to store level 6 or beyond
    #it takes more than 64 bits so that is incredibly chopped
    #lowk the hash is supposed to hash every state, so if a position has 20,000,000 states
    #you should be able to just hash that since 2^64 = 10^19
    def hash_ext(self, position: str) -> int:
        box_rank = get_combinadic_rank(box_indices)
        perfect_hash = (box_rank * total_valid_tiles) + valid_p_idx
        """
      
        """
        Returns a perfect hash using bitpacking.
        Only dynamic elements (Player and Boxes) are stored.

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
    """

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
    
    #helper functions
    def get_pos_idx(self, position: str):
        p_idx = position.find('@')
        if p_idx == -1:
            p_idx = position.find('+')
        return p_idx; 


def benchmark_sweep(variant_id="6", iterations=1000):
    print(f"--- Benchmarking Sokoban Variant {variant_id} ---")

    # 1. Initialize the game and get the starting position
    game = Sokoban(variant_id)
    position = game.start()

    # 2. Warm up (optional, but helps get past initial Python overhead)
    game.primitive(position)

    # 3. Start the clock
    start_time = time.perf_counter()

    # 4. Hammer the primitive function
    for _ in range(iterations):
        game.primitive(position)
        
    # 5. Stop the clock
    end_time = time.perf_counter()

    # 6. Crunch the numbers
    total_time = end_time - start_time
    ms_per_call = (total_time / iterations) * 1000
    states_per_second = iterations / total_time

    print(f"Total time for {iterations} checks: {total_time:.4f} seconds")
    print(f"Average time per primitive() call:  {ms_per_call:.4f} ms")
    print(f"States evaluated per second:        {states_per_second:,.0f} states/sec\n")

# Run the benchmark when you execute the file
if __name__ == "__main__":

    benchmark_sweep("1", 1000)
    
    # Let's do a stress test of 10,000 just for fun
    benchmark_sweep("1", 10000)

    benchmark_sweep("2", 1000)
    
    # Let's do a stress test of 10,000 just for fun
    benchmark_sweep("2", 10000)

    benchmark_sweep("3", 1000)
    
    # Let's do a stress test of 10,000 just for fun
    benchmark_sweep("3", 10000)

    benchmark_sweep("5", 1000)
    
    # Let's do a stress test of 10,000 just for fun
    benchmark_sweep("5", 10000)

    benchmark_sweep("6", 1000)
    
    # Let's do a stress test of 10,000 just for fun
    benchmark_sweep("6", 10000)