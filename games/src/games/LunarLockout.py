from models import Game, Value, StringMode
from typing import Optional

class LunarLockout(Game):
    id = 'lunarlockout'
    board_size = ["5x5"]
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
    # Store the variant and board dimensions (5x5).
    # Define constants: center square index (12), removed-robot value (31), and total robots (5).
    # Robot index 0 always represents the red robot.
    # Each robot position is encoded using 5 bits (values 0–31), producing a 25-bit packed state.
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
        # Exit Position
        self._center = self._cells // 2
        # Limits
        self._max_row = self._rows - 1
        self._max_col = self._cols - 1
        # Robot configs
        self._robot_count = len(self._config["robots"])
        self._red_index = 0
        self._removed = 31
        # Encoding
        self._bits_per_robot = 5
        self._mask = 0b11111
        # Directions
        self._directions = {
            self._move_up:    (-1, 0),
            self._move_right: ( 0, 1),
            self._move_down:  ( 1, 0),
            self._move_left:  ( 0, -1),
        }
        self._current_position = 0


    # Select starting squares for all robots with no duplicates.
    # Ensure the red robot is active and not already at a terminal condition.
    # Keep robot ordering consistent (red first).
    # Encode the five robot positions into a single integer state.
    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        robots = self._config["robots"].copy()
        # Validate: red not already winning
        if robots[self._red_index] == self._center:
            raise ValueError("Red cannot start at exit")
        # Optional (good practice): no duplicates
        if len(set(robots)) != len(robots):
            raise ValueError("Duplicate robot positions")
        return self.pack(robots)

    # Decode the state into robot positions.
    # Skip robots marked as removed (31).
    # Each remaining robot can be pushed in four directions (UP, RIGHT, DOWN, LEFT).
    # Encode moves as (robot_index * 4 + direction).
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
            if robots[robot_index] == self._removed:
                continue
            for direction in range(4):
                dest, _ = self._slide(robots, robot_index, direction)
                if dest != robots[robot_index]:
                    moves.append(robot_index * 4 + direction)

        return moves


    # Decode the state and identify the robot and direction from the move.
    # If the chosen robot is already removed, return the original state.
    # Slide in the chosen direction while staying aligned to the same row or column.
    # Stop when the nearest blocking robot is found.
    # If a blocker exists, stop immediately before it.
    # If the scan reaches the board edge with no blocker, the robot leaves the board and is marked removed (31).
    # Do not allow two active robots to occupy the same square.
    # Re-encode the updated positions into the new state.
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        robots = self.unpack(position)
        robot_index = move // 4
        direction = move % 4

        if robots[robot_index] == self._removed:
            return position

        dest, left_board = self._slide(robots, robot_index, direction)

        if left_board:
            robots[robot_index] = self._removed
        else:
            robots[robot_index] = dest

        return self.pack(robots)

    # Decode the state.
    # Return Win if the red robot occupies the center square (12).
    # Return Lose if the red robot has been removed (31).
    # Otherwise return None for a non-terminal position.
    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        robot_positions = self.unpack(position)
        red_position = robot_positions[self._red_index]

        if red_position == self._center:
            return Value.Win
        if red_position == self._removed:
            return Value.Loss
        
        return None

    # Convert the encoded state into a readable 5x5 board.
    # Display the center square and all active robots.
    # Do not display removed robots.
    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """ 
        robot_positions = self.unpack(position)
        board = [["-" for _ in range(self._cols)] for _ in range(self._rows)]
        symbols = [str(i) for i in range(self._robot_count)]

        for i, p in enumerate(robot_positions):
            if p == self._removed:
                continue
            row = p // self._cols
            col = p % self._cols
            board[row][col] = symbols[i]

        if mode == StringMode.AUTOGUI:
            return "1_" + "".join("".join(r) for r in board)
        if mode == StringMode.Readable:
            return "".join("".join(r) for r in board)

        return "\n".join(" ".join(r) for r in board)

    # Parse a readable board layout into robot positions.
    # Validate positions are within bounds and not duplicated.
    # Assign removed status to any robot not present.
    # Encode the positions into an integer state.
    def from_string(self, strposition: str) -> int:
        """
        Converts a readable board string into the encoded state.
        """
        strposition = strposition.replace("\\n", "\n")
        board = strposition.replace(" ", "").replace("\n", "")

        # Validate board size
        if len(board) != self._cells:
            raise ValueError("Invalid board size")

        robots = [self._removed] * self._robot_count


        for i, cell in enumerate(board):
            if cell.isdigit():
                idx = int(cell)
                # Reject robots outside allowed range
                if idx >= self._robot_count:
                    raise ValueError("Invalid robot index")
                # Check duplicate robot
                if robots[idx] != self._removed:
                    raise ValueError("Duplicate robot in board")
                robots[idx] = i

        # Red robot must exist
        if robots[self._red_index] == self._removed:
            raise ValueError("Red robot missing")

        return self.pack(robots)


    # Decode the move into robot index and direction.
    # Return a readable description of the movement direction.
    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        robot = move // 4
        direction = move % 4

        if mode == StringMode.AUTOGUI:
            robots = self.unpack(self._current_position)

            src = robots[robot]
            dest, _ = self._slide(robots, robot, direction)

            return f"M_{src}_{dest}"

        directions = ["u", "r", "d", "l"]
        return f"{robot} {directions[direction]}"
    

    def pack(self, robots: list[int]) -> int:
        """
        Takes the 5 robot positions and compresses them into one binary.

        robots must be a list in this exact order:
        [red, helper1, helper2, helper3, helper4]

        Each robot position is a number:
        0-24 = a square on the board
        31   = the robot has been removed

        We store each position using 5 bits.
        """
        state = 0
        # Add each robot position into the integer one at a time.
        # Shifting left makes space for the next robot, and the OR
        # places the new value into those 5 empty bits.
        for position in robots:
            if position < 0 or position > self._mask:
                raise ValueError("Invalid robot position")
            state = (state << self._bits_per_robot) | position
        return state


    def unpack(self, state: int) -> list[int]:
        """
        Reverses pack(): takes the encoded binary and recovers the
        original robot positions.

        Returns a list:
        [red, helper1, helper2, helper3, helper4]

        The function repeatedly reads the last 5 bits of the number to
        get a robot position, then shifts the number right to remove
        those bits.
        """
        robots = [0] * self._robot_count

        # Read robot locations backwards because the last robot inserted
        # is stored in the lowest 5 bits of the integer.
        for i in range(self._robot_count - 1, -1, -1):
            robots[i] = state & self._mask  # get last 5 bits
            state >>= self._bits_per_robot  # discard those bits
        return robots


    def _slide(self, robots: list[int], robot_index: int, direction: int):
        start_pos = robots[robot_index]

        curr_row = start_pos // self._cols
        curr_col = start_pos % self._cols

        delta_row, delta_col = self._directions[direction]

        last_valid_row = curr_row
        last_valid_col = curr_col
        exited_board = False

        while True:
            next_row = curr_row + delta_row
            next_col = curr_col + delta_col

            # Check if next step goes off the board
            if not (0 <= next_row < self._rows and 0 <= next_col < self._cols):
                exited_board = True
                break

            next_pos = next_row * self._cols + next_col

            # Check if next position is occupied by another robot
            if next_pos in robots and next_pos != start_pos:
                break

            # Advance to next valid position
            last_valid_row = next_row
            last_valid_col = next_col
            curr_row = next_row
            curr_col = next_col

        end_pos = last_valid_row * self._cols + last_valid_col
        return end_pos, exited_board