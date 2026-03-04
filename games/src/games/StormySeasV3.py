from models import Game, Value, StringMode
from typing import Optional

class StormySeas(Game):
    id = 'stormyseas'
    variants = ["a", "b", "c"]
    n_players = 1
    cyclic = False
    colors = ["R", "G", "O"]

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in StormySeas.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        board_rows = []

    def start(self) -> int:
        if self._variant_id == "a":
            self.board_rows = ["101011100","101110100","101101100","101011100","101011100","101110100","110110100","111011100"]

            # use ternary digits to represent shifts?
            curr_shift_string = "11000020"
            boat_pos = "123256227142" # first two digits are location, third digit is direction (1 = up, 2 = right, 3 = down, 4 = left), last digit is length
            hash = self.hash(curr_shift_string + boat_pos)
            return hash
        elif self._variant_id == "b":
            # Add variant b starting position
            string_rep = "010101111001011101010110110010101110010101110001011101000011011011110111001123238221142"
            return self.hash(string_rep)
        elif self._variant_id == "c":
            # Add variant c starting position
            string_rep = "010101111001011101010110110010101110010101110001011101000011011011110111001123238221142"
            return self.hash(string_rep)
        
        return 0
    
    def generate_moves(self, position: int):
        """
        Returns a list of positions given the input position.
        """
        string_rep = self.translate(self.unhash(position))
        list_to_return = []

        string_rep_list = list(string_rep)

        #DO NOT MODIFY THESE POSITIONS DIRECTLY
        board_list = string_rep_list[:72]
        boat_1 = string_rep_list[72:76]
        boat_2 = string_rep_list[76:80]
        boat_3 = string_rep_list[80:84]
        boat_list = [boat_1, boat_2, boat_3] 

        #up
        for boat in boat_list:
            current_pos = int(boat[0]) * 10 + int(boat[1])
            current_dir = int(boat[2])

            #up
            if current_dir == 1:
                if current_pos <= 9:
                    continue
                elif board_list[current_pos - 9 - 1] == '0':
                    new_board = board_list[:current_pos - 9 - 1] + ['1'] + board_list[current_pos - 9:current_pos - 1] + ['0'] + board_list[current_pos:]
                    new_boat = [str(current_pos - 9)] + boat[1:]
                    list_to_return.append(self.hash(self.untranslate((''.join(new_board) + ''.join(new_boat)))))
            #down
            elif current_dir == 3:
                if current_pos >= 64:
                    continue
                else:
                    if board_list[current_pos + 9 - 1] == '0':
                        new_board = board_list[:current_pos - 1] + ['0'] + board_list[current_pos:current_pos + 9 - 1] + ['1'] + board_list[current_pos + 9:]
                        new_boat = [str(current_pos + 9)] + boat[1:]
                        list_to_return.append(self.hash(self.untranslate((''.join(new_board) + ''.join(new_boat)))))

        # move row
        rowList = []
        for x in range(8):
            rowList.append(string_rep[9*x: 9*x + 9])
        
        for x in range(8):
            if rowList[x][0] == '0':
                modifiedRow = rowList[x][1:] + "0"
                modifiedPos = ''.join(rowList[0:x]) + modifiedRow + ''.join(rowList[(x+1):]) + string_rep[72:]
             
                modifiedPos = self.untranslate(modifiedPos)
             
                
                list_to_return.append(self.hash(modifiedPos))
            if rowList[x][8] == '0':
                modifiedRow = "0" + rowList[x][:8]
                modifiedPos = ''.join(rowList[0:x]) + modifiedRow + ''.join(rowList[(x+1):]) + string_rep[72:]
                list_to_return.append(self.hash(self.untranslate((modifiedPos))))

        # move boat left/right
        for boat in boat_list:
            current_dir = int(boat[2])
            current_length = int(boat[3])
            occupied_pos_1 = int(boat[0]) * 10 + int(boat[1])

            if current_dir == 1 or current_dir == 3:
                if current_dir == 1:
                    occupied_pos_2 = occupied_pos_1 + 9
                elif current_dir == 3:
                    occupied_pos_2 = occupied_pos_1
                    occupied_pos_1 = occupied_pos_1 - 9
                
                col_of_boat = occupied_pos_1 % 9 if occupied_pos_1 % 9 != 0 else 9
                col_of_boat_i = col_of_boat - 1 if col_of_boat != 9 else 8

                row_1 = (occupied_pos_1 - 1) // 9
                row_2 = (occupied_pos_2 - 1) // 9

                #moving left
                if col_of_boat_i > 0 and rowList[row_1][0] == '0' and rowList[row_2][0] == '0':
                    modifiedRow1 = rowList[row_1][1:] + "0"
                    modifiedRow2 = rowList[row_2][1:] + "0"
                    modified_pos = occupied_pos_1 - 1
                    modified_boat = [str(modified_pos)] + boat[1:]
                    
                    new_rowlist = rowList[:min(row_1, row_2)] + [modifiedRow1 if i == row_1 else modifiedRow2 if i == row_2 else rowList[i] for i in range(len(rowList))] + [modified_boat]
                    list_to_return.append(self.hash(self.untranslate(''.join(new_rowlist[0]))))
                    
                #moving right
                if col_of_boat_i < 8 and rowList[row_1][8] == '0' and rowList[row_2][8] == '0':
                    modifiedRow1 = "0" + rowList[row_1][:8]
                    modifiedRow2 = "0" + rowList[row_2][:8]
                    modified_pos = occupied_pos_1 + 1
                    modified_boat = [str(modified_pos)] + boat[1:]
                    
                    new_rowlist = rowList[:min(row_1, row_2)] + [modifiedRow1 if i == row_1 else modifiedRow2 if i == row_2 else rowList[i] for i in range(len(rowList))] + [modified_boat]
                    list_to_return.append(self.hash(self.untranslate((''.join(new_rowlist[0])))))

        return list_to_return
    
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

        # Check if any boat has reached position 69 facing down (direction 3)
        boats_start = 72
        for i in range(0, len(string_rep) - boats_start, 4):
            boat_data = string_rep[boats_start + i:boats_start + i + 4]
            if len(boat_data) >= 4:
                boat_pos = int(boat_data[:2])
                boat_dir = int(boat_data[2])
                if boat_pos == 69 and boat_dir == 3:
                    return Value.Win

        return None

    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        string_rep = self.translate(self.unhash(position))
        waveString = string_rep[:72]

        string_view = list(''.join(['.' if x == '0' else '~' for x in waveString])) # change these symbols

        boatString = string_rep[72:]
   
        i = 0
        color = 0
        while i <= len(boatString):
            if i + 4 > len(boatString):
                break
            boatSlice = boatString[i:i+4]
            boatPos = int(boatSlice[:2]) - 1 # Convert to index
            
            if boatPos < len(string_view):
                string_view[boatPos] = self.colors[color]

                boat_dir = int(boatSlice[2])
                # Mark the other part of the boat
                if boat_dir == 1 and boatPos + 9 < len(string_view):
                    string_view[boatPos + 9] = self.colors[color].lower()
                elif boat_dir == 2 and boatPos - 1 >= 0:
                    string_view[boatPos - 1] = self.colors[color].lower()
                elif boat_dir == 3 and boatPos - 9 >= 0:
                    string_view[boatPos - 9] = self.colors[color].lower()
                elif boat_dir == 4 and boatPos + 1 < len(string_view):
                    string_view[boatPos + 1] = self.colors[color].lower()
            color += 1
            i += 4

        string_view = ''.join(string_view)
        return "\n".join([string_view[9*x: 9*x + 9] for x in range(8)])

    def from_string(self, strposition: str) -> int:
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        # Remove newlines and convert readable symbols back to binary
        cleaned = strposition.replace("\n", "")
        binary_str = ''.join(['0' if c == '.' else '1' for c in cleaned if c in ['.', '~']])
    
        # Extract boat information from remaining characters
        boat_chars = [c for c in cleaned if c in self.colors or c in self.colors[0].lower()]
    
        # Convert boat characters to boat data (position, direction, length)
        boat_info = ""
        boat_positions = {}
    
        for idx, char in enumerate(cleaned):
            if char.upper() in self.colors:
                if char.upper() not in boat_positions:
                    boat_positions[char.upper()] = []
                boat_positions[char.upper()].append((idx + 1, char.isupper()))  # 1-indexed position, isupper=start
    
        # Build boat info string (4 digits per boat: position + direction + length)
        for color in self.colors:
            if color in boat_positions:
                positions = sorted(boat_positions[color])
                start_pos = min(p[0] for p in positions)
            
                # Determine direction and length
                if len(positions) > 1:
                    pos_list = [p[0] for p in positions]
                    if pos_list[1] - pos_list[0] == 9:  # vertical
                        direction = 1 if positions[0][1] else 3  # 1=up, 3=down
                    else:  # horizontal
                        direction = 2 if positions[0][1] else 4  # 2=right, 4=left
                else:  # single boat piece
                    direction = 1 if positions[0][1] else 3
            length = len(positions)
            
            boat_info += f"{start_pos:02d}{direction}{length}"
    
        return self.hash(self.translate((binary_str + boat_info)))

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        if mode == StringMode.Readable:
            return self.to_string(move, mode)
        return str(move)

    def hash(self, strPos: str) -> int:
        """
        Converts a string position to an integer hash.
        """

        # first 8 characters of strPos is the ternary rep of waves
        # rest are regular numbers, first convert these to ternary via boatTernary
        # put string back together, then the final string convert into an integer via int(x, 3)

        wavePosString = strPos[:8]
        boatString = strPos[8:]
        boatTernaryString = ""

        for i in range(0, len(boatString), 4):
           boat = boatString[i:i+4]
           boatTernaryString += self.boatTernary(boat)

        result = wavePosString + boatTernaryString

        return int(result, 3)
    
    def unhash(self, intPos: int) -> str:
        """
        Converts an integer hash back to a string position.
        """


        #turn integer back into ternary string VIA to ternary
        #first 8 digits are fine, boats are seperated via length 8 and turned back into their integer reps
        #then add everything together again

        strPos = str(self.toTernaryString(intPos))

        wavePosString = strPos[:8]
        boatTernaryString = strPos[8:]
        boatString = ""

        while boatTernaryString != "":
            boatString += self.boatTernaryReverse(boatTernaryString[:8])
            boatTernaryString = boatTernaryString[8:]

        return wavePosString + boatString
    
    def boatTernary(self, boatString: str) -> str:
        #turn the (string) integer rep of boats into ternary strings

        boatPos = self.toTernaryString(int(boatString[:2])).rjust(4, "0")
        boatDir = self.toTernaryString(int(boatString[2])).rjust(2, "0")
        boatLen = self.toTernaryString(int(boatString[3])).rjust(2, "0")

        result = boatPos + boatDir + boatLen
       
        return result
    
    def boatTernaryReverse(self, boatTernaryStr: str) -> str:
        #turn ternary string representations back into boat integers (but string)

        return str(int(boatTernaryStr[:4], 3)) + str(int(boatTernaryStr[4:6], 3)) + str(int(boatTernaryStr[6:], 3)) 

    
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

      
        shifts = [x for x in str[:8]]
        board = ""
        row = 0

        for x in shifts:
            if x == '0':
                board = board + self.board_rows[row]
            elif x == '1':
                board += "0" + self.board_rows[row][:8] 
            else:
                board += "00" + self.board_rows[row][:7]
            
            
            row += 1


        return board + str[8:]
    
    def untranslate(self, str):

        
        board_part = str[:72]
        boat_part = str[72:]
        
        shifts = ""
        for row_idx in range(8):
            row = board_part[row_idx * 9 : (row_idx + 1) * 9]
            expected_row = self.board_rows[row_idx]
            
            if row == expected_row:
                shifts += "0"
            elif row == "0" + expected_row[:8]:
                shifts += "1"
            elif row == "00" + expected_row[:7]:
                shifts += "2"

    
        return shifts + boat_part

    
        
        


