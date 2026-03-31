from models import Game, Value, StringMode

class ASnakesTale(Game):
    id = "snakestale1"
    n_players = 1
    cyclic = True
    variants = {"lvl1": {"board": "4x4",
                         "obstacle": [],
                         "pos_i": [7, 3, 2, 1],
                         "hole_pos": 12,
                         "length" : 4,
                         "water": [],
                         "land_snakes": [],
                         "water_snakes": []},
                "lvl2":{"board":"4x4",
                        "obstacle": [5, 7, 9, 13],
                        "pos_i": [0, 4, 8, 12],
                        "hole_pos": 12,
                        "length" : 4,
                        "water": [],
                        "land_snakes": [],
                        "water_snakes": []},
                "lvl3":{"board":"4x4",
                        "obstacle": [3],
                        "pos_i": [15, 11, 7],
                        "hole_pos": 12,
                        "length" : 3,
                        "water": [1, 2, 5],
                        "land_snakes": [8, 9, 13],
                        "water_snakes": [6, 10, 14]},
                "lvl4":{"board":"4x4",
                        "obstacle": [15],
                        "pos_i": [7, 3],
                        "hole_pos": 1,
                        "length": 2,
                        "water": [5, 9],
                        "land_snakes": [0, 4, 8, 12, 13, 14, 10, 6, 2],
                        "water_snakes": []
                        }}

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in ASnakesTale.variants:
            raise ValueError("Variant not defined")
        self.variant_id = variant_id
        variant_data = ASnakesTale.variants[variant_id]
        rows_str, cols_str = variant_data["board"].split('x')
        self.rows = int(rows_str)
        self.cols = int(cols_str)
        self.pos_i = variant_data["pos_i"]
        self.obstacle = variant_data["obstacle"]
        self.snake_len = variant_data["length"]
        self.hole_pos = variant_data["hole_pos"]
        self.water = variant_data.get("water", [])
        self.player = PlayerSnake(variant_data["pos_i"], variant_data["length"])
        self.obstacle_snakes = []
        if variant_data["land_snakes"]:
            ls = variant_data["land_snakes"]
            self.obstacle_snakes.append(LandSnake(ls, len(ls)))
        if variant_data["water_snakes"]:
            ws = variant_data["water_snakes"]
            self.obstacle_snakes.append(WaterSnake(ws, len(ws)))
        self.all_movable_snakes = [self.player] + self.obstacle_snakes

    def start(self) -> int:
        all_snakes = [s.cells for s in self.all_movable_snakes]
        return self.hash(all_snakes)

    def generate_moves(self, position: int) -> list[int]:
        all_snakes = self.unhash(position)
        total_cells = self.rows * self.cols
        moves = []
        for idx, snake_obj in enumerate(self.all_movable_snakes):
            snake_obj.cells = all_snakes[idx]
            for target in snake_obj.get_moves(self):
                moves.append(idx * total_cells + target)
        return moves
               
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        snake_idx, target = divmod(move, self.rows * self.cols)
        all_snakes = self.unhash(position)
        snake = all_snakes[snake_idx]
        all_snakes[snake_idx] = [target] + snake[:-1]
        return self.hash(all_snakes)

    def primitive(self, position: int):
        all_snakes = self.unhash(position)
        for i, s in enumerate(self.all_movable_snakes):
            s.cells = all_snakes[i]
        if all_snakes[0][0] == self.hole_pos:
            return Value.Win
        moves = self.generate_moves(position)
        if not moves:
            return Value.Loss
        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        all_snakes = self.unhash(position)
        total_cells = self.rows * self.cols
        board = ['-'] * total_cells
        board[self.hole_pos] = 'O'
        for obs in self.obstacle:
            board[obs] = 'X'
        for water_cell in self.water:
            board[water_cell] = '~'
        def get_dir(from_cell, to_cell):
            diff = to_cell - from_cell
            if diff == -self.cols:
                return 'U'
            if diff == self.cols:
                return 'D'
            if diff == 1:
                return 'R'
            if diff == -1:
                return 'L'
            return 'U'
            
        def head_char(cells, head_chars):
            head, neck = cells[0], cells[1] if len(cells) > 1 else None
            if neck is None:
                return head_chars['U']
            return head_chars.get(get_dir(neck, head), head_chars['U'])
        
        def body_char(cells, i, body_chars):
            d1 = get_dir(cells[i], cells[i - 1])
            d2 = get_dir(cells[i], cells[i + 1])
            key = ''.join(sorted([d1, d2]))
            return body_chars.get(key, next(iter(body_chars.values()))) 

        def tail_char(cells, tail_chars):
            if len(cells) < 2:
                return tail_chars['U']
            direction = get_dir(cells[-2], cells[-1])
            return tail_chars.get(direction, tail_chars['U'])
           
        player_heads = {'U': '^', 'D': 'v', 'L': 'i', 'R': 'r'}
        land_heads   = {'U': 'A', 'D': 'B', 'L': 'C', 'R': 'D'} # pick unused chars
        water_heads  = {'U': 'E', 'D': 'F', 'L': 'G', 'R': 'I'}

        player_body = {'DU': 'q', 'LR': 'p', 'DR': 'b', 'DL': 'c', 'RU': 'd', 'LU': 'e'}
        land_body   = {'DU': 'Q', 'LR': 'P', 'DR': 'M', 'DL': 'n', 'RU': 'H', 'LU': 'V'} # pick unused chars
        water_body  = {'DU': 'x', 'LR': 'y', 'DR': 'z', 'DL': 'f', 'RU': 'g', 'LU': 'u'}

        player_tail = {'U': 'T', 'D': 'J', 'L': 'K', 'R': 'N'}
        land_tail  = {'U': 'W', 'D': 'X', 'L': 'Y', 'R': 'Z'} # pick unused chars
        water_tail  = {'U': 'o', 'D': 'm', 'L': 't', 'R': 'j'}

        symbols = [(head_char, player_heads, player_body, player_tail),
                (head_char, land_heads, land_body, land_tail),
                (head_char, water_heads, water_body, water_tail)]
       
        for i, cells in enumerate(all_snakes):
            hc_fn, hc_map, bc_map, tc_map = symbols[i]
            for j, cell in enumerate(cells):
                if j == 0:
                    board[cell] = hc_fn(cells, hc_map)
                elif j == len(cells) - 1:
                    board[cell] = tail_char(cells, tc_map)
                else:
                    board[cell] = body_char(cells, j, bc_map)
        s = ''.join(board)
        rows_output = [s[i*self.cols:(i + 1)*self.cols] for i in range(self.rows)]
        if mode == StringMode.Readable:
            return ''.join(rows_output)
        elif mode == StringMode.AUTOGUI:
            return "1_" + ''.join(rows_output)
        s = '\n'.join(rows_output)
        return s

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        #flat = strposition.replace('\n', '')
        if not strposition or strposition.strip() == '':
            return self.start()
       
        flat = strposition.replace('\n', '')
        # Map each character back to snake index and segment role
        # Rebuild cell lists from board characters
        player_heads = {'^', 'v', 'i', 'r'}
        land_heads   = {'A', 'B', 'C', 'D'}
        water_heads  = {'E', 'F', 'G', 'I'}
       
        n = len(self.all_movable_snakes)
        # We'll reconstruct ordered cells by reading head direction + body
        # Strategy: find head, then follow neck->tail using adjacency
        cells_by_snake = [[] for _ in range(n)]
        head_positions = {}

        for i, ch in enumerate(flat):
            if ch in player_heads:
                head_positions[0] = i
            elif ch in land_heads:
                head_positions[1] = i
            elif ch in water_heads:
                head_positions[2] = i

        def follow_snake(head, snake_idx, segment_chars):
            cells = [head]
            current = head
            for _ in range(self.all_movable_snakes[snake_idx].length - 1):
                r, c = divmod(current, self.cols)
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        neighbor = nr * self.cols + nc
                        if neighbor not in cells and flat[neighbor] in segment_chars:
                            cells.append(neighbor)
                            current = neighbor
                            break
            return cells
        
        player_body_chars = {'q', 'p', 'b', 'c', 'd', 'e'}
        player_tail_chars = {'T', 'J', 'K', 'N'}
        land_body_chars   = {'Q', 'P', 'M', 'n', 'H', 'V'}
        land_tail_chars   = {'W', 'X', 'Y', 'Z'}
        water_body_chars  = {'x', 'y', 'z', 'f', 'g', 'u'}
        water_tail_chars  = {'o', 'm', 't', 'j'}

        body_tail_chars = [
            player_body_chars | player_tail_chars,
            land_body_chars   | land_tail_chars,
            water_body_chars  | water_tail_chars,
            ]
        
        for idx in range(n):
            if idx in head_positions:
                cells_by_snake[idx] = follow_snake(head_positions[idx], idx, body_tail_chars[idx])
        return self.hash(cells_by_snake)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        total_cells = self.rows * self.cols
        snake_idx, target = divmod(move, total_cells)
        if mode == StringMode.AUTOGUI:
            head = self.all_movable_snakes[snake_idx].cells[0]
            return f'M_{head}_{target}_x'
        r, c = divmod(target, self.cols)
        snake_names = ["Player", "LandSnake", "WaterSnake"]
        name = snake_names[snake_idx] if snake_idx < len(snake_names) else f"Snake{snake_idx}"
        return f"{name} ({r}, {c})"
   
        #total_cells = self.rows * self.cols
        #snake_idx, target = divmod(move, total_cells)
        #if mode == StringMode.AUTOGUI:
        #    return f'M_{move}_{target}_x' # change move to to current state
        #r, c = divmod(target, self.cols)
        #snake_names = ["Player", "LandSnake", "WaterSnake"]
        #name = snake_names[snake_idx] if snake_idx < len(snake_names) else f"Snake{snake_idx}"
        #return f"{name} ({r}, {c})"
   
    def hash(self, all_snakes: list[list[int]]) -> int:
        """
        Encodes all snake positions as a single integer.
        Each cell index is a 'digit' in base total_cells.
        """
        total_cells = self.rows * self.cols
        result = 0
        for snake_cells in all_snakes:
            for cell in snake_cells:
                result = result * total_cells + cell
        return result

    def unhash(self, position: int) -> list[list[int]]:
        """
        Decodes a position integer back into snake cell lists.
        """
        total_cells = self.rows * self.cols
        all_snakes = []
        # Decode in reverse order
        for snake in reversed(self.all_movable_snakes):
            cells = []
            for _ in range(snake.length):
                position, cell = divmod(position, total_cells)
                cells.append(cell)
            all_snakes.append(list(reversed(cells)))
        return list(reversed(all_snakes))


       
class Snake:
    def __init__(self, cells, length):
        self.cells = cells        
        self.length = length
           
    def can_enter(self, cell: int, board) -> bool:
        if cell in self.cells[:-1]:
            return False
        if cell in board.obstacle:
            return False
        for s in board.all_movable_snakes:
            if s is not self and cell in s.cells:
                return False
        return True
   
    def get_moves(self, board):
        head = self.cells[0]
        r, c = divmod(head, board.cols)
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board.rows and 0 <= nc < board.cols:
                target = nr * board.cols + nc
                if self.can_enter(target, board):
                    moves.append(target)
        return moves    
   
    def move(self, new_head: int) -> list[int]:
        return [new_head] + self.cells[:-1]
       
class PlayerSnake(Snake):
    def can_enter(self, cell, board):
        if cell == board.hole_pos:
            return True  # always allow player to enter the hole
        return super().can_enter(cell, board)
       
class WaterSnake(Snake):
    def can_enter(self, cell, board):
        if not super().can_enter(cell, board):  
            return False
        return True

class LandSnake(Snake):
    def can_enter(self, cell, board):
        if not super().can_enter(cell, board):
            return False
        if cell in board.water:
            return False
        return True