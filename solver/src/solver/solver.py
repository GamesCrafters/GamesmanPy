from collections import deque, defaultdict
from models import *
from database import DuckDB, SqliteDB
import time

REMOTENESS_TERMINAL = 0
REMOTENESS_DRAW = 255

class Solver:
    def __init__(self, game: Game):
        self._game = game
        self.solution = {}
        self.parent_map = defaultdict(list)
        self.unsolved_children = {}

    def solve(self, overwrite=False, variant=None):
        variants = []
        if variant is None:
            variants = self._game.variants
        else:
            variants = [variant]

        for variant in variants:
            self.solution = {}
            self.parent_map = defaultdict(list)
            self.unsolved_children = {}
            self.game = self._game(variant)
            self.db = SqliteDB(self._game.id, variant, ro=False)
            if overwrite or not self.db.exists:
                print("----------------------------------")
                print(f"Solving {self.game.id}, variant: {variant}")
                print("Creating database file")
                self.db.create_table(overwrite)
                print("Discovering primitive positions")
                start = time.perf_counter()
                self.discover()
                end = time.perf_counter()
                elapsed = end - start
                print(f"Discovered primitive positions in {elapsed:.2f}s")
                print("Propagating remoteness")
                self.propagate()
                self.resolve_draws()
                end = time.perf_counter()
                elapsed = end - start
                print(f"Solved {self.game.id}, variant: {variant} in {elapsed:.2f}s")
                print("Writing to database...")
                self.db.insert(self.solution)
                print(f'{len(self.solution)} positions written to database')
            else:
                print(f"{self.game.id}, variant: {variant} already solved.")

    def get_children(self, position, generate_moves, do_move):
        moves = generate_moves(position)
        children = list(map(lambda m: do_move(position, m), moves))
        return children

    def discover(self):
        visited = set()
        q = deque()
        start = self.game.start()

        no_hash = hasattr(self.game, "no_hash")
        hash_ext = self.game.hash_ext
        primitive = self.game.primitive
        do_move = self.game.do_move
        gen_moves = self.game.generate_moves
        n_players = self.game.n_players

        q.appendleft(start)
        if no_hash is None:
            visited.add(hash_ext(start))
        else:
            visited.add(start)
        while q:
            position = q.popleft()
            hashed_position = hash_ext(position)
            value = primitive(position)
            if value is not None:
                self.solution[hashed_position] = (REMOTENESS_TERMINAL, value)
                self.unsolved_children[hashed_position] = 0
            else:
                children = self.get_children(position, gen_moves, do_move)    
                if not children and n_players == 1:
                    self.solution[hashed_position] = (REMOTENESS_TERMINAL, Value.Loss)

                for child in children:
                    hashed_child = hash_ext(child)
                    child_alt = hashed_child if no_hash is None else child
                    if hashed_child != hashed_position:
                        self.parent_map[hashed_child].append(hashed_position)
                        prev_unsolved = self.unsolved_children.get(hashed_position, 0)
                        self.unsolved_children[hashed_position] = prev_unsolved + 1
                    if child_alt not in visited:
                        visited.add(child_alt)
                        q.append(child)


    def propagate(self):
        wins = deque()
        ties = deque()
        losses = deque()

        for pos, (_, val) in self.solution.items():
            match val:
                case Value.Win: wins.append(pos)
                case Value.Tie: ties.append(pos)
                case Value.Loss: losses.append(pos)
        while wins or ties or losses:
            hashed_position = None
            if losses:
                hashed_position = losses.popleft()
            elif wins:
                hashed_position = wins.popleft()
            else:
                hashed_position = ties.popleft()
            (curr_rem, curr_val) = self.solution[hashed_position]
            parent_rem = curr_rem + 1
            parent_val: Value = self.parent_value(curr_val)
            parents = self.parent_map.get(hashed_position, [])
            for hashed_parent in parents:
                unsolved_children = self.unsolved_children[hashed_parent]
                if unsolved_children == 0:
                    continue
                if parent_val == Value.Loss:
                    self.unsolved_children[hashed_parent] -= 1
                else:
                    self.unsolved_children[hashed_parent] = 0
                
                if self.unsolved_children[hashed_parent] == 0:
                    self.solution[hashed_parent] = (parent_rem, parent_val)
                    match parent_val:
                        case Value.Win: wins.append(hashed_parent)
                        case Value.Tie: ties.append(hashed_parent)
                        case Value.Loss: losses.append(hashed_parent)

    def resolve_draws(self):
        for pos_hash in self.unsolved_children.keys():
            if self.game.n_players == 2:
                if self.unsolved_children[pos_hash] > 0:
                    self.solution[pos_hash] = (REMOTENESS_DRAW, Value.Draw)
            else:
                if pos_hash not in self.solution or self.unsolved_children[pos_hash] > 0:
                    self.solution[pos_hash] = (REMOTENESS_DRAW, Value.Loss)
            
    
    def parent_value(self, val: Value) -> Value:
        if self._game.n_players == 1:
            return val
        else:
            if val == Value.Win:
                return Value.Loss
            elif val == Value.Loss:
                return Value.Win
            else:
                return val
