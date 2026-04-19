from models import Game, Value, StringMode
from typing import Optional

class LunarLockout(Game):
    id = 'lunarlockout'
    board_size = ["7x7"]
    n_players = 1
    cyclic = False

    _move_up = 0
    _move_right = 1
    _move_down = 2
    _move_left = 3

    variants = {
        "beginner": {
            "robots": [20, 7, 16, 0, 23],
        },
        "easy": {
            "robots": [21, 2, 4, 11, 18],
        },
        "medium": {
            "robots": [2, 0, 4, 20, 24],
        },
        "hard": {
            "robots": [24, 2, 4, 10, 18, 20],
        }
    }

    # Robot index 0 always represents the red robot.
    # Each robot position is encoded using 6 bits (values 0–63)
    # Prepare any movement direction offsets needed for row/column stepping.
    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in LunarLockout.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._config = LunarLockout.variants[variant_id]
        # Board dimensions
        size_string = LunarLockout.board_size[0]
        self._rows, self._cols = map(int, size_string.split("x"))
        self._cells = self._rows * self._cols 
        # playable region bounds
        self._min = 1
        self._max = self._rows - 2
        # dynamic center (works for any odd board)
        center_row = self._rows // 2
        center_col = self._cols // 2
        self._center = center_row * self._cols + center_col
        # encoding must support positions up to 48 (7x7 board)
        self._bits_per_robot = 6
        self._mask = 0b111111
        # inactive marker (must fit in mask)
        self._inactive = 63
        # Robot configs
        self._robot_count = len(self._config["robots"])
        self._red_index = 0
        # Directions
        self._directions = {
            self._move_up:    (-1, 0),
            self._move_right: ( 0, 1),
            self._move_down:  ( 1, 0),
            self._move_left:  ( 0, -1),
        }
        self._current_position = 0


    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        robots = self._config["robots"].copy()
        # Optional (good practice): no duplicates
        if len(set(robots)) != len(robots):
            raise ValueError("Duplicate robot positions")
        shifted = []
        # shifts 5x5 inside 7x7
        for p in robots:
            r = p // 5
            c = p % 5
            shifted.append((r + 1) * self._cols + (c + 1))
        return self.pack(shifted)


    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        A move is encoded as:
        move = robot_index * 4 + direction
        Directions:
            0 = UP
            1 = RIGHT
            2 = DOWN
            3 = LEFT
        Move:
            robot index 0 = 0-3
                        1 = 4-7
                        ....
        """
        robots = self.unpack(position)
        moves = []
        self._current_position = position

        for robot_index in range(self._robot_count):
            pos = robots[robot_index]
            if pos == self._inactive or self._is_border(pos):
                continue
            for direction in range(4):
                dest = self._slide(robots, robot_index, direction)
                if dest != pos:
                    moves.append(robot_index * 4 + direction)
        return moves


    def do_move(self, position: int, move: int) -> int:
        """
        Applies a move by sliding the selected robot in the given direction.
        Robots in the border or inactive state cannot move. If a robot lands
        in the border (space), it replaces any robot already there.
        """
        robots = self.unpack(position)
        robot_index = move // 4
        direction = move % 4
        pos = robots[robot_index]

        if pos == self._inactive or self._is_border(pos):
            return position
        dest = self._slide(robots, robot_index, direction)
        if self._is_border(dest):
            for i in range(self._robot_count):
                if i != robot_index and robots[i] == dest:
                    robots[i] = self._inactive
        robots[robot_index] = dest
        return self.pack(robots)


    def primitive(self, position: int) -> Optional[Value]:
        """
        Determines if the position is terminal:
        win if the red robot reaches the center, loss if it reaches the border,
        otherwise the position is non-terminal.
        """
        robots = self.unpack(position)
        red = robots[self._red_index]
        if red == self._center:
            return Value.Win
        if self._is_border(red):
            return Value.Loss
        return None


    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the 7x7 board.
        Border cells represent space; inner cells are the playable area.
        """
        robots = self.unpack(position)

        # Create full 7x7 board
        board = [["-" for _ in range(self._cols)] for _ in range(self._rows)]
        symbols = [str(i) for i in range(self._robot_count)]

        for i, p in enumerate(robots):
            if p == self._inactive:
                continue
            row = p // self._cols
            col = p % self._cols
            board[row][col] = symbols[i]

        if mode == StringMode.AUTOGUI:
            return "1_" + "".join("".join(r) for r in board)
        if mode == StringMode.Readable:
            return "".join("".join(r) for r in board)

        return "\n".join(" ".join(r) for r in board)


    def from_string(self, strposition: str) -> int:
        """
        Converts a 7x7 board string into the encoded state.
        """
        strposition = strposition.replace("\\n", "\n")
        board = strposition.replace(" ", "").replace("\n", "")

        # Must match 7x7
        if len(board) != self._cells:
            raise ValueError("Invalid board size")
        robots = [self._inactive] * self._robot_count

        for i, cell in enumerate(board):
            if cell.isdigit():
                idx = int(cell)
                if idx >= self._robot_count:
                    raise ValueError("Invalid robot index")
                if robots[idx] != self._inactive:
                    raise ValueError("Duplicate robot in board")
                robots[idx] = i

        # Red robot must exist
        if robots[self._red_index] == self._inactive:
            raise ValueError("Red robot missing")

        return self.pack(robots)


    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        robot = move // 4
        direction = move % 4
        if mode == StringMode.AUTOGUI:
            robots = self.unpack(self._current_position)
            src = robots[robot]
            dest = self._slide(robots, robot, direction)
            return f"M_{src}_{dest}"
        
        directions = ["u", "r", "d", "l"]
        return f"{robot} {directions[direction]}"
    

    def pack(self, robots: list[int]) -> int:
        """
        Compresses robot positions into a single integer.
        Each robot position is stored using 6 bits (values 0–63),
        allowing representation of the full 7x7 board plus inactive state.
        """
        state = 0
        # Add each robot position into the integer one at a time.
        # Shifting left makes space for the next robot, and the OR
        # places the new value into those 6 empty bits.
        for position in robots:
            if position < 0 or position > self._mask:
                raise ValueError("Invalid robot position")
            state = (state << self._bits_per_robot) | position
        return state


    def unpack(self, state: int) -> list[int]:
        """
        Reverses pack(): extracts robot positions from the encoded integer.
        Each robot position occupies 6 bits.
        """
        robots = [0] * self._robot_count

        # Read robot locations backwards because the last robot inserted
        # is stored in the lowest 6 bits of the integer.
        for i in range(self._robot_count - 1, -1, -1):
            robots[i] = state & self._mask  # get last 6 bits
            state >>= self._bits_per_robot  # discard those bits
        return robots

    def _is_border(self, pos: int) -> bool:
        """
        Returns True if the position is on the outer edge of the board.
        Border cells represent space (terminal region) and are not part of the playable area.
        """

        if pos == self._inactive:
            return False

        row = pos // self._cols
        col = pos % self._cols

        return (
            row == 0 or row == self._rows - 1 or
            col == 0 or col == self._cols - 1
        )

    def _slide(self, robots: list[int], robot_index: int, direction: int):
        """
        Slides a robot in the given direction until it hits a blocker
        or reaches the border. Border cells are allowed and terminate movement.
        """
        start_pos = robots[robot_index]
        # Cannot move inactive or border robots
        if start_pos == self._inactive or self._is_border(start_pos):
            return start_pos

        curr_row = start_pos // self._cols
        curr_col = start_pos % self._cols
        delta_row, delta_col = self._directions[direction]
        last_row = curr_row
        last_col = curr_col

        while True:
            next_row = curr_row + delta_row
            next_col = curr_col + delta_col
            if not (0 <= next_row < self._rows and 0 <= next_col < self._cols):
                break
            next_pos = next_row * self._cols + next_col
            # Block only if robot is active and not in border
            blocked = False
            for rpos in robots:
                if rpos == next_pos and rpos != self._inactive and not self._is_border(rpos):
                    blocked = True
                    break
            if blocked:
                break
            curr_row = next_row
            curr_col = next_col
            last_row = curr_row
            last_col = curr_col
            # Stop if we reach border
            if self._is_border(next_pos):
                break
        return last_row * self._cols + last_col