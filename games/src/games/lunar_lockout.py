from models import Game, Value, StringMode
from typing import Optional

class LunarLockout(Game):
    id = 'lunar_lockout'
    variants = ["5x5"]
    n_players = 1
    cyclic = True
    _move_up = 0b00
    _move_down = 0b10
    _move_right = 0b01
    _move_left = 0b11

    # Store the variant and board dimensions (5x5).
    # Define constants: center square index (12), removed-robot value (31), and total robots (5).
    # Robot index 0 always represents the red robot.
    # Prepare any movement direction offsets needed for row/column stepping.
    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in LunarLockout.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._cols = int(variant_id[0])
        self._rows = int(variant_id[2])
        self.board_size = [int(i) for i in self._variant_id.split(sep="x")]


    # Select starting squares for all robots with no duplicates.
    # Ensure the red robot is active and not already at a terminal condition.
    # Keep robot ordering consistent (red first).
    # Encode the five robot positions into a single integer state.
    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        pass
    

    # Decode the state into robot positions.
    # Skip robots marked as removed (31).
    # For each active robot, attempt movement in the four directions.
    # Movement must stay within the same row for left/right and same column for up/down.
    # While scanning, consider only the nearest active robot as a blocker.
    # Add a move for every direction; absence of a blocker means the robot will leave the board.
    # Encode moves as (robot_index * 4 + direction).
    def generate_moves(self, position: int) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        pass
    

    # Decode the state and identify the robot and direction from the move.
    # If the chosen robot is already removed, return the original state.
    # Slide in the chosen direction until the nearest blocking robot is found.
    # If a blocker exists, stop immediately before it.
    # If no blocker exists, mark the robot as removed (31).
    # Do not allow two active robots to occupy the same square.
    # Re-encode the updated positions into the new state.
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        pass


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
        pass


    # Parse a readable board layout into robot positions.
    # Validate positions are within bounds and not duplicated.
    # Assign removed status to any robot not present.
    # Encode the positions into an integer state.
    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        pass


    # Decode the move into robot index and direction.
    # Return a readable description of the movement direction.
    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        pass

    
    # Helper responsibilities:
    # Provide pack and unpack functions converting between the integer state and the five robot positions.
    # Convert between index and (row, column) coordinates.
    # Provide stepping logic for movement along rows and columns.
    # Provide alignment checks for same-row and same-column detection.