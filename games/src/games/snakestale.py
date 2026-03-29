from models import Game, Value, StringMode

class Snakestale(Game):
    id = "snakestale"
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
    n_players = 1
    cyclic = True

    def __init__(self, variant_id: str):
        if variant_id not in Snakestale.variants:
            raise ValueError("variant not defined")
        self.variant_id = variant_id
        variant_data = Snakestale.variants[variant_id]
        rows_str, cols_str = variant_data["board"].split("x")
        self.cols = int(cols_str)
        self.rows = int(rows_str)
        self.pos_i = variant_data["pos_i"]
        self.obstacle = variant_data["obstacle"]
        self.snake_len = variant_data["length"]
        self.hole_pos = variant_data["hole_pos"]
        self.bits = (self.rows * self.cols).bit_length()
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

    
    def start(self):
        # pos_str = self.pos_i
        # pos = self.hash(pos_str)
        # return pos
        all_snakes = [s.cells for s in self.all_movable_snakes]
        return self.hash_all(all_snakes)

    def generate_moves(self, position: int):
        # snake = self.unhash(position)
        # head = snake[0]
        # r, c = divmod(head, self.cols)

        # moves =[]
        # for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        #     nr, nc = r + dr, c + dc
        #     if 0 <= nr < self.rows and 0 <= nc < self.cols:
        #         target = nr * self.cols + nc
        #         if target not in snake[:-1] and target not in self.obstacle:
        #             moves.append(target)
        # return moves +
        all_snakes = self.unhash_all(position)
        total_cells = self.rows * self.cols
        moves = []
        for idx, snake_obj in enumerate(self.all_movable_snakes):
            snake_obj.cells = all_snakes[idx]
            for target in snake_obj.get_moves(self):
                moves.append(idx * total_cells + target)
        return moves



    def do_move(self, position: int, move):
        snake_idx, target = divmod(move, self.rows * self.cols)
        all_snakes = self.unhash_all(position)
        snake = all_snakes[snake_idx]
        all_snakes[snake_idx] = [target] + snake[:-1]
        return self.hash_all(all_snakes)


    def primitive(self, position: int):
        all_snakes = self.unhash_all(position)
        if all_snakes[0][0] == self.hole_pos:
            return Value.Win
        if not self.generate_moves(position):
            return Value.Loss

        
    def to_string(self, position: int, mode: StringMode) -> str:
        all_snakes = self.unhash_all(position)
        total_cells = self.rows * self.cols
        board = ['-'] * total_cells
        board[self.hole_pos] = 'O'
        for obs in self.obstacle:
            board[obs] = 'X'
        for water_cell in self.water:
            board[water_cell] = '~'
        def head_char(cells, head_chars):
            head, neck = cells[0], cells[1] if len(cells) > 1 else None
            if neck is None:
                return head_chars['U']
            diff = head - neck
            if diff == -self.cols:
                return head_chars['U']
            if diff == self.cols:
                return head_chars['D']
            if diff == -1:
                return head_chars['L']
            if diff == 1:
                return head_chars['R']
            return head_chars['U']
        player_heads = {'U': '^', 'D': 'v', 'L': '<', 'R': '>'}
        land_heads   = {'U': 'A', 'D': 'B', 'L': 'C', 'R': 'D'}  # pick unused chars
        water_heads  = {'U': 'E', 'D': 'F', 'L': 'G', 'R': 'I'}
        symbols = [
        (head_char, player_heads, 's', 'T'),
        (head_char, land_heads,   'l', 'l'),
        (head_char, water_heads,  'w', 'w'),]
        for i, cells in enumerate(all_snakes):
            hc_fn, hc_map, mid, t = symbols[i]
            for j, cell in enumerate(cells):
                if j == 0:
                    board[cell] = hc_fn(cells, hc_map) 
                elif j == len(cells) - 1:
                    board[cell] = t
                else:
                    board[cell] = mid
        
        s = ''.join(board)
        rows_output = [s[i*self.cols:(i + 1)*self.cols] for i in range(self.rows)]
        if mode == StringMode.Readable:
            return ''.join(rows_output)
        elif mode == StringMode.AUTOGUI:
            return "1_" + ''.join(rows_output)
        s = '\n'.join(rows_output)
        return s

    def from_string(self, strposition: str) -> int:
        flat = strposition.replace('\n', '')

        def parse_snake(length, head_syms, body_syms):
            cells = [None] * length
            for cell_idx, label in enumerate(flat):
                if label in head_syms:
                    cells[0] = cell_idx
                elif label in body_syms:
                    for slot in range(1, length):
                        if cells[slot] is None:
                            cells[slot] = cell_idx
                            break
            return cells

        all_snakes = [parse_snake(self.snake_len, {'^', 'v', '<', '>'}, {'s', 'T'})]
        obs_symbols =  [({'A', 'B', 'C', 'D'}, {'l'}), ({'E', 'F', 'G', 'I'}, {'w'})]
        for i, obs_snake in enumerate(self.obstacle_snakes):
            if i < len(obs_symbols): 
                h_syms, b_syms = obs_symbols[i] 
            else:
                h_syms, b_syms = ({'?'}, {'?'})
            all_snakes.append(parse_snake(obs_snake.length, h_syms, b_syms))
        return self.hash_all(all_snakes)

    def move_to_string(self, move: int, mode: StringMode) -> str:
        snake_idx, target = divmod(move, self.rows * self.cols)
        if mode == StringMode.AUTOGUI:
            return f'A_-_{move}_x'
        head = self.all_movable_snakes[snake_idx].cells[0]
        diff = target - head
        if diff == -self.cols:
            direction = 'up'
        elif diff == self.cols:
            direction = 'down'
        elif diff == - 1:
            direction = 'left'
        else:
            direction = 'right'
        names = ['Player', 'Land', 'Water']
        name = names[snake_idx] if snake_idx < len(names) else f'snake{snake_idx}'
        return f'{name}snake: {direction}'
    
    
    def hash_all(self, all_snakes: list[list]):
        position = 0
        for snake_cells in all_snakes:
            for cell in snake_cells:
                position = (position << self.bits) | cell
        return position
    
    def unhash_all(self, position):
        lengths = [s.length for s in self.all_movable_snakes]
        total_cells = sum(lengths)
        mask = (1 << self.bits) - 1
        flat = []
        for i in range(total_cells):
            flat.append(position & mask)
            position >>= self.bits
        flat.reverse()
        result = []
        idx = 0
        for length in lengths:
            result.append(flat[idx:idx + length])
            idx += length
        return result
    
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
        if not super().can_enter(cell, board): 
            return False
        return True
        
class WaterSnake(Snake):
    def can_enter(self, cell, board):
        if not super().can_enter(cell, board):  
            return False
        if cell == board.hole_pos:
            return False
        return True

class LandSnake(Snake):
    def can_enter(self, cell, board):
        if not super().can_enter(cell, board):
            return False
        if cell in board.water: 
            return False
        return True