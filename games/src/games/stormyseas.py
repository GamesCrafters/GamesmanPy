
# THIS FUNCTION IS DEFUNCT, PLEASE LOOK AT STORMYSEASSMALL INSTEAD


from models import Game, Value, StringMode
from typing import Optional

class StormySeas(Game):
    id = 'stormyseas'
    variants = ["a", "regular"]  # 'regular' maps to 'a' in the API
    n_players = 1
    cyclic = False
    colors = ["R", "B"]

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in StormySeas.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self.board_rows = []
        self.default_rows = []
        self.boat_pos = []
        self.row_length = 0
        self.num_rows = 0
        self.win_condition = ""  # Example win condition

    def start(self) -> int:
        if self._variant_id in ("a", "regular"):
            self.default_rows = ["1011100","1010100","1101100","1011100","1110100"]
            self.board_rows = ["0101110","0101010","0011011","0101110","0111010"]

            # use ternary digits to represent shifts?
            curr_shift_string = "11211"
            boat_pos = ["24", "12"] # first two digits is position in row-col where 0, 0 is top left square on board (always facing DOWN and always length 2)
            self.boat_pos = boat_pos
            
            self.row_length = len(self.board_rows[0])
            self.num_rows = len(self.board_rows)
            self.win_condition = "43"


            for x in boat_pos:
                curr_shift_string += x

            hash = self.hash(curr_shift_string) #need to change/account for
            return hash

        return 0

    def rowsWithBoats(self):
        rows_w_boats = []
        for i in range(len(self.boat_pos)):
            pos_1 = int(self.boat_pos[i][0])
            pos_2 = pos_1 - 1
            if pos_1 not in rows_w_boats:
                rows_w_boats.append(pos_1)
            if pos_2 >= 0 and pos_2 not in rows_w_boats:  # guard against -1
                rows_w_boats.append(pos_2)
        return rows_w_boats


    def rowsMoveableLeft(self):
        rows_moveable_left = list(range(0, self.num_rows))
        for i in range(len(self.board_rows)):
            if int(self.board_rows[i][0]) == 1:
                rows_moveable_left.remove(i)

        return rows_moveable_left


    def rowsMoveableRight(self):
        rows_moveable_right = list(range(0, self.num_rows))
        for i in range(0, self.num_rows):
            if int(self.board_rows[i][self.row_length - 1]) == 1:
                rows_moveable_right.remove(i)

        return rows_moveable_right


    def overlappingRows(self):
        overlapping_rows = []
        # Compare as ints, not strings
        b0_row = int(self.boat_pos[0][0])
        b1_row = int(self.boat_pos[1][0])

        # Boats overlap if their occupied rows intersect
        # boat occupies rows: [bottom, bottom-1]
        b0_rows = {b0_row, b0_row - 1}
        b1_rows = {b1_row, b1_row - 1}

        if b0_rows & b1_rows:  # non-empty intersection
            overlapping_rows = list(b0_rows | b1_rows)

        return overlapping_rows

    def moveRowsRight(self, rows):
        stringToReturn = ""
        for orig_row_i in range(0, self.num_rows):
            if orig_row_i in rows:
                stringToReturn += "0" + self.board_rows[orig_row_i][:self.row_length - 1]
            else:
                stringToReturn += self.board_rows[orig_row_i]
        
        return stringToReturn

    def moveRowsLeft(self,rows):
        stringToReturn = ""
        for orig_row_i in range(0, self.num_rows):
            if orig_row_i in rows:
                stringToReturn += self.board_rows[orig_row_i][1:] + "0"
            else:
                stringToReturn += self.board_rows[orig_row_i]
        
        return stringToReturn

    def returnRows(self):
        stringToReturn = ""
        
        for orig_row in self.board_rows:
            stringToReturn += orig_row

        return stringToReturn
    

    def generate_moves(self, position: int):
        string_rep = self.translate(self.unhash(position))
        self.board_rows = [string_rep[i:i+7] for i in range(0, 35, 7)]
        # Also update boat_pos from the position
        boat_str = string_rep[35:]
        self.boat_pos = [boat_str[i:i+2] for i in range(0, len(boat_str), 2)]

        positions = []
        leftable_rows = self.rowsMoveableLeft()
        rightable_rows = self.rowsMoveableRight()
        touchable_rows = self.rowsWithBoats()
        overlapping_rows = self.overlappingRows()

        # 1. Move any non-boat row left
        for row in range(0, self.num_rows):
            if row not in touchable_rows and row in leftable_rows:
                stringToReturn = self.moveRowsLeft([row])
                for bp in self.boat_pos:
                    stringToReturn += bp
                positions.append(self.hash(self.untranslate(stringToReturn)))

        # 2. Move any non-boat row right
        for row in range(0, self.num_rows):
            if row not in touchable_rows and row in rightable_rows:
                stringToReturn = self.moveRowsRight([row])
                for bp in self.boat_pos:
                    stringToReturn += bp
                positions.append(self.hash(self.untranslate(stringToReturn)))

        # 3. Move any boat left (rows move left, boat col decreases)
        if overlapping_rows:
            if all(row in leftable_rows for row in overlapping_rows):
                stringToReturn = self.moveRowsLeft(overlapping_rows)
                for bp in self.boat_pos:
                    col = int(bp[1]) - 1
                    if col < 0:
                        col = self.row_length - 1
                    stringToReturn += bp[0] + str(col)
                positions.append(self.hash(self.untranslate(stringToReturn)))
        else:
            for boat_i in range(len(self.boat_pos)):
                bp = self.boat_pos[boat_i]
                rows = [int(bp[0]), int(bp[0]) - 1]
                if all(row in leftable_rows for row in rows) and int(bp[1]) > 0:
                    stringToReturn = self.moveRowsLeft(rows)
                    for j, other_bp in enumerate(self.boat_pos):
                        if j == boat_i:
                            stringToReturn += other_bp[0] + str(int(other_bp[1]) - 1)
                        else:
                            stringToReturn += other_bp
                    positions.append(self.hash(self.untranslate(stringToReturn)))

        # 4. Move any boat right (rows move right, boat col increases)
        if overlapping_rows:
            if all(row in rightable_rows for row in overlapping_rows):
                stringToReturn = self.moveRowsRight(overlapping_rows)
                for bp in self.boat_pos:
                    col = int(bp[1]) + 1
                    if col > self.row_length - 1:
                        col = 0
                    stringToReturn += bp[0] + str(col)
                positions.append(self.hash(self.untranslate(stringToReturn)))
        else:
            for boat_i in range(len(self.boat_pos)):
                bp = self.boat_pos[boat_i]
                rows = [int(bp[0]), int(bp[0]) - 1]
                if all(row in rightable_rows for row in rows) and int(bp[1]) < self.row_length - 1:
                    stringToReturn = self.moveRowsRight(rows)
                    for j, other_bp in enumerate(self.boat_pos):
                        if j == boat_i:
                            stringToReturn += other_bp[0] + str(int(other_bp[1]) + 1)
                        else:
                            stringToReturn += other_bp
                    positions.append(self.hash(self.untranslate(stringToReturn)))

        # 5. Slide any boat up or down
        for boat_i in range(len(self.boat_pos)):
            bp = self.boat_pos[boat_i]
            row = int(bp[0])
            col = int(bp[1])

            # The board is translated (shifted), so col indexes correctly into board_rows
            # Move down: check row+1 exists and is empty
            if row < self.num_rows - 1 and self.board_rows[row + 1][col] == '0':
                stringToReturn = self.returnRows()
                for j, other_bp in enumerate(self.boat_pos):
                    if j == boat_i:
                        stringToReturn += str(row + 1) + str(col)
                    else:
                        stringToReturn += other_bp
                positions.append(self.hash(self.untranslate(stringToReturn)))

            # Move up: top cell is at row-1, new top would be row-2
            if row > 0 and self.board_rows[row - 2][col] == '0':
                stringToReturn = self.returnRows()
                for j, other_bp in enumerate(self.boat_pos):
                    if j == boat_i:
                        stringToReturn += str(row - 1) + str(col)
                    else:
                        stringToReturn += other_bp
                positions.append(self.hash(self.untranslate(stringToReturn)))

        return positions
        
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        # If move is already a position (from generate_moves), return it directly
        # Otherwise, this could be an index into the moves list
        possible_moves = self.generate_moves(position)
        if isinstance(move, int) and 0 <= move < len(possible_moves):
            return possible_moves[move]
        return move

    def primitive(self, position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        string_rep = self.translate(self.unhash(position))

        boats_start = 35
        if (string_rep[(self.row_length * self.num_rows):(self.row_length * self.num_rows + 2)] == self.win_condition):
                    return Value.Win
        return None

    def CoordinateToPosition(self, x: int, y: int) -> int:
        return x + y * self.row_length  # board is row_length columns wide

    def to_string(self, position: int, mode: StringMode) -> str:
        
        string_rep = self.translate(self.unhash(position))
        waveString = string_rep[:self.row_length * self.num_rows]
        boatString = string_rep[self.row_length * self.num_rows:]

        # pretend that the center of each tile is a wave or not
        if mode == StringMode.AUTOGUI:
            #translate the waves
            waves = ['W' if char == '0' else '-' for char in waveString]
            #translate the boats; need to be coordinates in fashion of coords
            boat = []
            red_row = int(boatString[0]);
            red_col = int(boatString[1]);
            blue_row = int(boatString[2]);
            blue_col = int(boatString[3]);
            for i in range(0, 7):
                for j in range(0, 5):
                    if j == red_row and i == red_col:
                        boat += ['R']
                    elif j == blue_row and i == blue_col:
                        boat += ['B']
                    else:
                        boat += ['-']

            stringWave = ""
            for string in waves:
                stringWave += string
            
            stringBoat = ""
            for string in boat:
                stringBoat += string

            return "1_" + stringWave + stringBoat
    
        elif mode == StringMode.READABLE:

            
        # Build base grid from wave data
            string_view = list(''.join(['~' if x == '1' else '.' for x in waveString]))

            i = 0
            color = 0
            while i + 2 <= len(boatString):
                boatSlice = boatString[i:i+2]
                row = int(boatSlice[0])  # bottom cell row
                col = int(boatSlice[1])  # column

                bottom_idx = self.CoordinateToPosition(col, row)
                top_idx = self.CoordinateToPosition(col, row - 1)

                if 0 <= bottom_idx < self.row_length * self.num_rows and 0 <= top_idx < self.row_length * self.num_rows:
                    string_view[bottom_idx] = self.colors[color].upper()  # bottom = uppercase
                    string_view[top_idx] = self.colors[color].lower()     # top = lowercase

                color += 1
                i += 2

            string_view = ''.join(string_view)
            return "\n".join([string_view[self.row_length*x: self.row_length*x + self.row_length] for x in range(self.num_rows)])

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        # Ensure the game is initialized with required dimensions
        if self.num_rows == 0 or self.row_length == 0:
            # Initialize with variant "a" defaults
            if self._variant_id in ("a", "regular"):
                self.default_rows = ["1011100","1010100","1101100","1011100","1110100"]
                self.board_rows = ["0101110","0101010","0011011","0101110","0111010"]
                self.boat_pos = ["24", "12"]
                self.row_length = len(self.board_rows[0])
                self.num_rows = len(self.board_rows)
                self.win_condition = "43"
        
        rows = strposition.split("\n")
        binary_str = ""
        boat_positions = {}  # color -> (row, col) of bottom cell

        for row_idx, row in enumerate(rows):
            for col_idx, char in enumerate(row):
                if char == '~':
                    binary_str += '1'
                elif char == '.':
                    binary_str += '0'
                elif char.upper() in self.colors:
                    binary_str += '0'  # boat cell is not a wave
                    if char.isupper():  # uppercase = bottom cell
                        boat_positions[char.upper()] = (row_idx, col_idx)
                else:
                    binary_str += '0'  # fallback

        # Build boat_pos list in the same order as self.colors
        boat_pos_list = []
        for color in self.colors:
            if color in boat_positions:
                row, col = boat_positions[color]
                boat_pos_list.append(f"{row}{col}")

        # Combine binary board + boat positions, then untranslate and hash
        full_string = binary_str + "".join(boat_pos_list)
        return self.hash(self.untranslate(full_string))
    
    
    def move_to_string(self, move: int, mode: StringMode) -> str:
        if mode != StringMode.Readable:
            return str(move)

        # Get current board state from self.board_rows and self.boat_pos
        # (already set by the most recent generate_moves call)
        move_rep = self.translate(self.unhash(move))
        move_rows = [move_rep[i:i+self.row_length] for i in range(0, self.row_length * self.num_rows, self.row_length)]
        move_boat_str = move_rep[self.row_length * self.num_rows:]
        move_boats = [move_boat_str[i:i+2] for i in range(0, len(move_boat_str), 2)]

        curr_rows = self.board_rows
        curr_boats = self.boat_pos

        # Check if any boat moved
        for boat_i, (curr_bp, move_bp) in enumerate(zip(curr_boats, move_boats)):
            curr_row, curr_col = int(curr_bp[0]), int(curr_bp[1])
            move_row, move_col = int(move_bp[0]), int(move_bp[1])
            color = self.colors[boat_i].lower()

            if curr_col != move_col or curr_row != move_row:
                if curr_row != move_row:
                    direction = "down" if move_row > curr_row else "up"
                    return f"boat{color}-{direction}"
                else:
                    direction = "left" if move_col < curr_col else "right"
                    return f"boat{color}-{direction}"

        # Otherwise a wave row moved
        for row_i, (curr_row, move_row) in enumerate(zip(curr_rows, move_rows)):
            if curr_row != move_row:
                if move_row == curr_row[1:] + "0":
                    return f"row{row_i}-left"
                else:
                    return f"row{row_i}-right"

        return str(move)  # fallback

    def hash(self, strPos: str) -> int:
        """
        Converts a string position to an integer hash.
        """

        # strPos format: shifts (num_rows chars) + boats (2 chars per boat)
        # The boats are in decimal format (e.g. "24" for row 2, col 4), convert to ternary
        
        wavePosString = strPos[:self.num_rows]
        boatString = strPos[self.num_rows:]
        boatTernaryString = ""

        for i in range(0, len(boatString), 2):
           boat = boatString[i:i+2]
           boatTernaryString += self.boatTernary(boat)

        result = wavePosString + boatTernaryString

        return int(result, 3)

    def unhash(self, intPos: int) -> str:
        # Ensure the game is initialized with required dimensions
        if self.num_rows == 0 or len(self.boat_pos) == 0:
            # Initialize with variant "a" defaults
            if self._variant_id in ("a", "regular"):
                self.default_rows = ["1011100","1010100","1101100","1011100","1110100"]
                self.board_rows = ["0101110","0101010","0011011","0101110","0111010"]
                self.boat_pos = ["24", "12"]
                self.row_length = len(self.board_rows[0])
                self.num_rows = len(self.board_rows)
                self.win_condition = "43"
        
        total_length = self.num_rows + 5 * len(self.boat_pos)  # 5 shifts + 5 ternary digits per boat
        strPos = self.toTernaryString(intPos).rjust(total_length, "0")

        wavePosString = strPos[:self.num_rows]
        boatTernaryString = strPos[self.num_rows:]
        boatString = ""

        while boatTernaryString != "":
            boatString += self.boatTernaryReverse(boatTernaryString[:5])
            boatTernaryString = boatTernaryString[5:]

        return wavePosString + boatString

    def boatTernary(self, boatString: str) -> str:
        # Convert 2-digit decimal boat position to fixed 5-digit ternary
        # max boat position is 46 (row 4, col 6) = ternary "1201" = 4 digits, so 5 is safe
        boatPos = self.toTernaryString(int(boatString)).rjust(5, "0")
        return boatPos

    def boatTernaryReverse(self, boatTernaryStr: str) -> str:
        # Convert 5-digit ternary back to 2-digit decimal string, zero-padded
        return str(int(boatTernaryStr, 3)).rjust(2, "0")


    def toTernaryString(self, n):
        if n == 0:
            return "0"

        tern_digits = []
        while n:
            remainder = n % 3
            tern_digits.append(str(remainder))
            n = n // 3

        tern_str = "".join(tern_digits[::-1])

        return tern_str

    def translate(self, str):
        #turn the shifts into a board :sob:


        shifts = [x for x in str[:self.num_rows]]
        board = ""
        for row, x in enumerate(shifts):
            if x == '0':
                board = board + self.default_rows[row]
            elif x == '1':
                board += "0" + self.default_rows[row][:self.row_length - 1] 
            else:
                board += "00" + self.default_rows[row][:self.row_length - 2]

        return board + str[self.num_rows:]

    def untranslate(self, str):


        board_part = str[:(self.num_rows * self.row_length)]
        boat_part = str[self.num_rows * self.row_length:]

        shifts = ""
        for row_idx in range(self.num_rows):
            row = board_part[row_idx * self.row_length : (row_idx + 1) * self.row_length]
            expected_row = self.default_rows[row_idx]

            if row == expected_row:
                shifts += "0"
            elif row == "0" + expected_row[:self.row_length - 1]:
                shifts += "1"
            elif row == "00" + expected_row[:self.row_length - 2]:
                shifts += "2"


        return shifts + boat_part