from collections import deque
from models import *
from database import GameDB
import time

REMOTENESS_TERMINAL = 0
REMOTENESS_DRAW = 255

class AcyclicSolver:
    def __init__(self, game: Game):
        self._game = game
        self.solution = {}
        self.parent_map = {}
        self.unsolved_children = {}

    def solve(self, overwrite=False, variant=None):
        variants = []
        if variant is None:
            variants = self._game.variants
        else:
            variants = [variant]

        for variant in variants:
            self.game = self._game(variant)
            self.db = GameDB(self._game.id, variant, ro=False)
            if overwrite or not self.db.exists:
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
                print(len(self.solution))
            else:
                print(f"{self.game.id}, variant: {variant} already solved.")

    def get_children(self, position):
        moves = self.game.generate_moves(position)
        return list(map(lambda m: self.game.do_move(position, m), moves))

    def discover(self):
        visited = set()
        q = deque()
        start = self.game.start()
        q.appendleft(start)
        visited.add(start)
        while q:
            position = q.pop()
            value = self.game.primitive(position)
            if value is not None:
                self.solution[position] = (REMOTENESS_TERMINAL, value)
                self.unsolved_children[position] = 0
            else:
                children = self.get_children(position)
                self.unsolved_children[position] = len(children)
                for child in children:
                    if not self.parent_map.get(child):
                        self.parent_map[child] = set()
                    self.parent_map[child].add(position)
                    if child not in visited:
                        visited.add(child)
                        q.appendleft(child)
    
    def propagate(self):
        wins = deque()
        ties = deque()
        losses = deque()
        for pos, (_, val) in self.solution.items():
            match val:
                case Value.Win: wins.appendleft(pos)
                case Value.Tie: ties.appendleft(pos)
                case Value.Loss: losses.appendleft(pos)
        while wins or ties or losses:
            position = None
            if losses:
                position = losses.pop()
            elif wins:
                position = wins.pop()
            else:
                position = ties.pop()
            (curr_rem, curr_val) = self.solution.get(position)
            parent_rem = curr_rem + 1
            parent_val: Value = self.parent_value(curr_val)
            parents = self.parent_map.get(position, set())
            for parent in parents:
                unsolved_children = self.unsolved_children[parent]
                if unsolved_children == 0:
                    continue
                if parent_val == Value.Loss:
                    self.unsolved_children[parent] = unsolved_children - 1
                else:
                    self.unsolved_children[parent] = 0
                ex_parent_sol = self.solution.get(parent)
                if ex_parent_sol is None:
                    self.solution[parent] = (parent_rem, parent_val)
                else:
                    (ex_parent_rem, ex_parent_val) = ex_parent_sol
                    propagate = False
                    if ex_parent_val < parent_val:
                        propagate = True
                    elif ex_parent_val == parent_val:
                        if ex_parent_val == Value.Loss:
                            if ex_parent_rem < parent_rem:
                                propagate = True
                        elif ex_parent_rem > parent_rem:
                            propagate = True
                    if propagate:
                        self.solution[parent] = (parent_rem, parent_val)
                if self.unsolved_children[parent] == 0:
                    (_, p_val) = self.solution[parent]
                    match p_val:
                        case Value.Win: wins.appendleft(parent)
                        case Value.Tie: ties.appendleft(parent)
                        case Value.Loss: losses.appendleft(parent)
                    

    def resolve_draws(self):
        for pos in self.unsolved_children.keys():
            if self.unsolved_children[pos] > 0:
                self.solution[pos] = (REMOTENESS_DRAW, Value.Draw)
    
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
    
    def print(self):
        if self.solution:
            sol = [(position, rem, value) for position, (rem, value) in self.solution.items()]
        else:
            sol = self.db.get_all()
        for (position, rem, value) in sol:
            print(f'state: {self.game.to_string(position, StringMode.Readable)} | remoteness: {rem} | value: {Value(value).name}')
    
    def get_remoteness(self, state: int) -> int:
        rem, _ = self.db.get(state)
        if rem is None:
            return -1
        return rem
