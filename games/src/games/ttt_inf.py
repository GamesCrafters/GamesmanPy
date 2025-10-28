from models import Game, Value, StringMode
from typing import Optional
from abc import abstractmethod

class TTT_inf(Game):
    id = 'ttt-inf'
    variants = ['default']
    n_players = 2
    cyclic = False

    @abstractmethod
    def start() -> int:
        return 0
    
    @abstractmethod
    def generate_moves(position: int) -> list[int]:
        move_age = 0b001
        free = []
        mask_token = 0b1000
        mask_age = 0b111
        piece_shift = 4
        player = 0b0
        for i in range(9):
            age = position & mask_age
            token = (position & mask_token) >> 3
            if age == 0b000:
                free.append(i)
            elif age == 0b001:
                player = token ^ 0b1
            position >>= piece_shift
        moves = []
        for index in free:
            curr_move = (player << 3) | move_age
            curr_move <<= index * piece_shift
            moves.append(curr_move)
        return moves
    
    @abstractmethod
    def do_move(position: int, move: int) -> int:
        """
        Returns the resulting position of applying move to position.
        """
        mask_full = 0b1111_1111_1111_1111_1111_1111_1111_1111_1111
        mask_piece = 0b1111
        piece_shift = 4
        mask_token = 0b1000
        mask_age = 0b111
        new_pos = position
        shift = 0
        # Increment age
        for i in range(9):
            age = (position & mask_age) >> shift
            if age >= 0b110:
                new_pos &= mask_full ^ mask_piece
            elif age != 0b000:
                new_pos &= mask_full ^ mask_age
                new_age = age + 1
                new_pos |= new_age << shift
            mask_age <<= piece_shift
            mask_piece <<= piece_shift
            mask_token <<= piece_shift
            shift += piece_shift
        # Do move
        new_pos |= move
        return new_pos

    @abstractmethod
    def get_piece(index: int, position: int) -> str:
        corrected_index = 8 - index
        shift = corrected_index * 4
        token_mask = 0b1000
        age_mask = 0b111
        position >>= shift
        if (position & age_mask) == 0b000:
            return '-'
        player = position & token_mask
        if player == 0b0000:
            return 'x'
        return 'o'
    
    @abstractmethod
    def get_piece_detailed(index: int, position: int) -> str:
        corrected_index = 8 - index
        shift = corrected_index * 4
        token_mask = 0b1000
        age_mask = 0b111
        position >>= shift
        age = position & age_mask
        if (age) == 0b000:
            return '--'
        player = position & token_mask
        if player == 0b0000:
            return 'x' + str(age)
        return 'o' + str(age)
    
    @abstractmethod
    def get_turn(position: int) -> str:
        mask_token = 0b1000
        mask_age = 0b111
        piece_shift = 4
        player = 0b0
        for i in range(9):
            age = position & mask_age
            token = (position & mask_token) >> 3
            if age == 0b001:
                player = token
                break
            position >>= piece_shift
        return 'x' if player == 0 else 'o'
    
    @abstractmethod
    def to_string(position: int, mode: StringMode) -> str:
        board = []
        for i in range(9):
            board.append(TTT_inf.get_piece_detailed(i, position))
        if mode == StringMode.Readable:
            return '|'.join(board)
        player = TTT_inf.get_turn(position)
        autoGUI_player = '1_' if player == 'x' else '2_'
        return autoGUI_player + ''.join(TTT_inf.piece_to_char(piece) for piece in board)

    
    @abstractmethod
    def from_string(stringpos: str) -> int:
        arr = stringpos.split(',')
        pos = 0
        for piece in arr:
            pos <<= 4
            token = 1 if piece[0] == 'o' else 0
            age = 0 if piece[1] == '-' else int(piece[1])
            pos |= token << 3
            pos |= age
        return pos
    
    @abstractmethod
    def move_to_string(move: int, mode: StringMode) -> str:
        age_mask = 0b111
        index = 8
        while move & age_mask == 0b000:
            move >>= 4
            index -= 1
        move >>= 3
        if mode == StringMode.Readable:
            return f'{'x' if move == 0 else 'o'},{index}'
        return f'A_-_{index}_x'

    @abstractmethod
    def check_three(i1: int, i2: int, i3: int, position: int) -> bool:
        first = TTT_inf.get_piece(i1, position)
        return first != '-' and first == TTT_inf.get_piece(i2, position) and first == TTT_inf.get_piece(i3, position)
        
    @abstractmethod
    def primitive(position: int) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        piece_shift = 4
        row_shift = 12
        token_mask = 0b1000
        age_mask = 0b111
        pos_tmp = position
        for row in range(3):
            i = row * 3
            if TTT_inf.check_three(i, i + 1, i + 2, position):
                return Value.Loss
        
        for col in range(3):
            i = col
            if TTT_inf.check_three(i, i + 3, i + 6, position):
                return Value.Loss
            
        if TTT_inf.check_three(0, 4, 8, position):
            return Value.Loss
        if TTT_inf.check_three(2, 4, 6, position):
            return Value.Loss
        return None

    @abstractmethod
    def piece_to_char(piece: str) -> str:
        if piece == '--':
            return '-'
        base_char = '1' if piece[0] == 'x' else 'a'
        age = int(piece[1])
        return chr(ord(base_char) + age - 1)

            
    