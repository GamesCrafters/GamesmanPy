from models import Game, Value, StringMode
from typing import Optional

EMPTY, X, O = 0, 1, 2 # integers for cell status
CHARS = ['-', 'X', 'O'] # chars for cell status

RING = [0, 1, 2, 5, 8, 7, 6, 3] # ring of cell numbers around the board
CENTER = 4
NEIGHBORS = [None] * 9 # list of 9 elements
for idx, cell in enumerate(RING):
    NEIGHBORS[cell] = [RING[idx - 1], RING[(idx + 1) % 8], CENTER] # creating adjacency list
NEIGHBORS[CENTER] = RING[:] # all elems adjacent to center

# winning lines below
DIAMETERS = [(0, 4, 8), (2, 4, 6), (3, 4, 5), (1, 4, 7)]
RIM_LINES = [(RING[i], RING[(i+1) % 8], RING[(i+2) % 8]) for i in range(8)]
LINES = DIAMETERS + RIM_LINES # winning positions



class Rota(Game):
    id = 'rota'
    variants = ["regular"]
    n_players = 2
    cyclic = True

    def __init__(self, variant_id: str):
        """
        Define instance variables here (i.e. variant information)
        """
        if variant_id not in Rota.variants:
            raise ValueError("Variant not defined")
        self._variant_id = variant_id
        self._lines = LINES


    def _unpack(self, position : int) -> tuple[list[int], int]:
        """_summary_
        takes in the position int and performs bitwise operations to 
        get turn num and position list

        Args:
            position (int): integer storing board position and turn

        Returns:
            tuple[list[int], int]: tuple containing board state, int containing turn num
        """
        
        turn = position & 1 #isolates last bit of the position aka the turn num
        position = position >> 1 #get rid of final turn bit
        board = []
        

        # will shift bits of position by 2 every iteration, since 2 bits to store each cell
        # take those bits rightmost and append them to board
    
        for i in range(9):
            board.append(position & 0b11) # mask to get last two bits of pos
            position = position >> 2 #shift off curr cell bits
        return board, turn


    def _pack(self, board: list[int], turn: int) -> int:
        """_summary_
    
            Args:
                board (list[int]): list with integers to represent the pieces on the board
                turn (int): 0 or 1, whose turn it is
    
            Returns:
                int: 19 bit integer with whose turn it is and positions of pieces on board
    
            takes in board as list and turn (0 or 1) and encodes those into 19 bit
            value where first bit is whose turn (0 or 1) and rest is what piece in which
            position (01 is X, 10 is 0, 00 is empty)
            Ex. (0b1000000000000000010) means X turn and X in position 0, O in position 8
            """         
        position = turn
        for i in range(9):
            position |= board[i] << (2 * i + 1)
        return position

    def _decode_move(self, move : int) -> tuple:
        """_summary_

        takes in move and returns tuple with from and to cells
        
        Args:
            move (int): integer containing next move information

        Returns:
            tuple: contains source and destination of move. source is None if placement phase
        """
        if move < 10:
            # placement phase
            return None, move
        m = move - 10 # first digit becomes cell num from 0-8
        return m // 10, m % 10 # returns from (first dig), and two (second dig)
        

    def start(self) -> int:
        """
        Returns the starting position of the game.
        """
        return 0
    
    def generate_moves(self, position: int) -> list[int]:
        """_summary_
        Returns a list of positions given the input position.

        Args:
            position (int): position integer for board

        Returns:
            list[int]: list of ints containing legal moves
        """
        if self.primitive(position) is not None:
            return []

        board, turn = self._unpack(position)
        filled_cells = 0
        for cell in board:
            if cell != EMPTY:
                filled_cells += 1

        if filled_cells < 6:
            return [i for i in range(9) if board[i] == EMPTY]

        moves = []
        if turn == 0:
            # X's turn
            for i in range(len(board)):
                if board[i] == X:
                    moves.extend([10 + i*10 + n for n in NEIGHBORS[i] if board[n] == EMPTY])
        else:
            for i in range(len(board)):
                if board[i] == O:
                    moves.extend([10 + i*10 + n for n in NEIGHBORS[i] if board[n] == EMPTY])
        return moves
    
    
    def do_move(self, position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        board, turn = self._unpack(position)
        source, destination = self._decode_move(move)
        if source == None:
            if turn == 0:
                board[destination] = X
            else:
                board[destination] = O
        else:
            board[source] = EMPTY
            board[destination] = X if turn == 0 else O

        return self._pack(board, 1 - turn)

    def primitive(self, position: int) -> Optional[Value]:
        """_summary_

        Args:
            position (int): position and turn, is a 19 bit integer

        Returns:
            primitive value: Loss if there is a winning position for the opponent on this turn, else None
        """
        board, turn = self._unpack(position)
        for row in self._lines:
            if (board[row[0]] == board[row[1]] == board[row[2]] ) and board[row[1]] != EMPTY:
                return Value.Loss
        return None
            
    def to_string(self, position: int, mode: StringMode) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        board, turn = self._unpack(position)
        cells = ''.join(CHARS[c] for c in board)

        if mode == StringMode.AUTOGUI:
            return ('1_' if turn == 0 else '2_') + cells

        if mode == StringMode.TUI:
            return self._render_tui(board, turn)

        return cells + ('X' if turn == 0 else 'O')

    def from_string(self, strposition: str) -> int:
        """_summary_
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.

        Args:
            strposition (str): "----------" first 9 chars are board, last char is turn

        Returns:
            int: board position in int
        """
        board = [CHARS.index(strposition[i]) for i in range(9)]
        
        turn = 0 if strposition[-1] == 'X' else 1
        return self._pack(board, turn)

    def _render_tui(self, board, turn):
        characters = [ CHARS[board[i]] if board[i] != EMPTY else "●" for i in range(9)]
        _ART = [
            f"      ╭── {characters[1]} ──╮",
            f"     ╱    │    ╲",
            f"    {characters[0]}     │     {characters[2]}",
            f"  ╱    ╲  │  ╱    ╲",
            f"{characters[3]} ─────── {characters[4]} ─────── {characters[5]}",
            f"  ╲    ╱  │  ╲    ╱",
            f"    {characters[6]}     │     {characters[8]}",
            f"     ╲    │    ╱",
            f"      ╰── {characters[7]} ──╯",
            f"",
            f"Turn: {'X' if turn == 0 else 'O'}",
            f""
        ]
        return "\n".join(_ART)



        

    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        source , destination = self._decode_move(move)
        if mode == StringMode.AUTOGUI:
            if source == None:
                return f'A_-_{destination}_x'
            else:
                return f'M_{source}_{destination}_x'
        if source == None:
            return f'{destination}'
        else:
            return f'{source}-{destination}'

    