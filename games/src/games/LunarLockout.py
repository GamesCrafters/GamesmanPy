from models import Game, Value, StringMode
from typing import Optional

class LunarLockout(Game):
    id = 'lunar_lockout'
    variants = ["puzzle1"]
    board_size = ["5x5"]
    n_players = 1
    cyclic = True

    _move_up = 0
    _move_down = 1
    _move_right = 2
    _move_left = 3

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

        # Board dimensions
        size_string = LunarLockout.board_size[0]
        self._rows, self._cols = map(int, size_string.split("x"))
        self._cells = self._rows * self._cols
        # Exit Position
        self._center = self._cells // 2
        # Limits
        self._max_row = self._rows - 1
        self._max_col = self._cols - 1
        self.row_stride = self._cols # for jumping through rows

        # Robot configs
        self._robot_count = 5
        self._red_index = 0
        self._removed = 31
        # Encoding
        self._bits_per_robot = 5
        self._mask = 0b11111
        # Directions
        self._directions = {
            self._move_up:    (-1, 0),
            self._move_down:  ( 1, 0),
            self._move_left:  ( 0, -1),
            self._move_right: ( 0, 1),
        }


    # Select starting squares for all robots with no duplicates.
    # Ensure the red robot is active and not already at a terminal condition.
    # Keep robot ordering consistent (red first).
    # Encode the five robot positions into a single integer state.
    def start(self) -> int:
        """
        Returns the starting position of the game.
        """

        # # All values must be 0–24 and no duplicates.
        # red = 0
        # r1 = 4
        # r2 = 20
        # r3 = 24
        # r4 = 12
        # robots = [red, r1, r2, r3, r4]
        # return self.pack(robots)
        red = 0
        helpers = [6, 8, 16, 18]
        if red == 12:
            raise ValueError("Red cannot start at exit")

        return self.pack([red] + helpers)
    

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
        for robot_index in range(self._robot_count):
            # Skip robots that have been removed
            if robots[robot_index] == self._removed:
                continue
            # Each active robot can attempt all four directions
            for direction in range(4):
                move = robot_index * 4 + direction
                moves.append(move)
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
        robot_positions = self.unpack(position)
        # Get new robot position and direction
        robot_index = move // 4 # 7/4 = index 1
        direction = move % 4    # 7%4 = direction 3

        # Handle removed robot
        if robot_positions[robot_index] == self._removed:
            return position
        
        # Current Robot position
        cell = robot_positions[robot_index]
        row = cell // self._cols
        col = cell % self._cols
        # Move Direction Step
        move_row, move_col = self._directions[direction] # Gives step by step movements

        # Move Robots
        while True:
            next_row = row + move_row
            next_col = col + move_col

            # Handle robot getting out of space
            if not (0 <= next_row < self._rows and 0 <= next_col < self._cols):
                robot_positions[robot_index] = self._removed
                break

            next_cell = next_row * self._cols + next_col

            # Move robot until block
            blocked = False
            for i in range(self._robot_count):
                if i != robot_index and robot_positions[i] == next_cell:
                    blocked = True
                    break
            if blocked:
                break

            row = next_row
            col = next_col

        if robot_positions[robot_index] != self._removed:
            robot_positions[robot_index] = row * self._cols + col

        return self.pack(robot_positions)


    # Decode the state.
    # Return Win if the red robot occupies the center square (12).
    # Return Lose if the red robot has been removed (31).
    # Otherwise return None for a non-terminal position.
    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        pass


    # Convert the encoded state into a readable 5x5 board.
    # Display the center square and all active robots.
    # Do not display removed robots.
    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        robots = unpack(position)

        board = [["." for _ in range(5)] for _ in range(5)]
        board[2][2] = "X"       
        symbols = ["R", "A", "B", "C", "D"]     
        for i, pos in enumerate(robots):
            if pos == 31:
                continue
            r = pos // 5
            c = pos % 5
            board[r][c] = symbols[i]        
        return "\n".join(" ".join(row) for row in board)


    # Parse a readable board layout into robot positions.
    # Validate positions are within bounds and not duplicated.
    # Assign removed status to any robot not present.
    # Encode the positions into an integer state.
    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        lines = strposition.strip().split("\n")

        robots = [31, 31, 31, 31, 31]       
        symbol_map = {
        "R": 0,
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4
        }       
        for r in range(5):
            cells = lines[r].split()
            for c in range(5):
                cell = cells[c]
                if cell in symbol_map:
                    idx = r * 5 + c
                    robots[symbol_map[cell]] = idx      
        return self.pack(robots)     

    # Decode the move into robot index and direction.
    # Return a readable description of the movement direction.
    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        robot = move // 4
        direction = move % 4

        directions = ["UP", "RIGHT", "DOWN", "LEFT"]

        if robot == 0:
            name = "Red"
        else:
            name = f"Robot {robot}"

        return f"{name} {directions[direction]}"

    
    # Helper responsibilities:
    # Provide pack and unpack functions converting between the integer state and the five robot positions.
    # Pack and unpack must be exact inverses and produce a single canonical representation of every board state.
    # Convert between index and (row, column) coordinates.
    # Provide stepping logic for movement along rows and columns.
    # Provide alignment checks for same-row and same-column detection.

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