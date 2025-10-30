from collections import deque
from models import *
from database import GameDB
import time

REMOTENESS_TERMINAL = 0

class AcyclicSolver:
    def __init__(self, game: Game):
        self._game = game
        self.solution = {}
        self.parent_map = {}
        self.unsolved_children = {}

    def solve(self, overwrite=False):
        for variant in self._game.variants:
            self.game = self._game(variant)
            self.db = GameDB(self._game.id, variant)
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
                end = time.perf_counter()
                elapsed = end - start
                print(f"Solved {self.game.id}, variant: {variant} in {elapsed:.2f}s")
                print("Writing to database...")
                self.db.insert(self.solution)
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
                #print(f'Found terminal position: {self.game.to_string(position, StringMode.Readable)}')
                self.solution[position] = (REMOTENESS_TERMINAL, value)
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
        q = deque(self.solution.keys())
        while q:
            position = q.pop()
            (curr_rem, curr_val) = self.solution.get(position)
            parent_rem = curr_rem + 1
            parent_val: Value = self.parent_value(curr_val)
            parents = self.parent_map.get(position, set())
            for parent in parents:
                self.unsolved_children[parent] = self.unsolved_children[parent] - 1
                if self.unsolved_children[parent] == 0:
                    q.appendleft(parent)
                ex_parent_sol = self.solution.get(parent)
                if ex_parent_sol is None:
                    self.solution[parent] = (parent_rem, parent_val)
                else:
                    (ex_parent_rem, ex_parent_val) = ex_parent_sol
                    propagate = False
                    if ex_parent_val < parent_val:
                        #print(f'replacing value {ex_parent_val} with {parent_val}')
                        propagate = True
                    elif ex_parent_val == parent_val:
                        if ex_parent_val == Value.Loss:
                            if ex_parent_rem < parent_rem:
                                #print(f'{ex_parent_val}: replacing rem {ex_parent_rem} with {parent_rem}')
                                propagate = True
                        elif ex_parent_rem > parent_rem:
                            #print(f'{ex_parent_val}: replacing rem {ex_parent_rem} with {parent_rem}')
                            propagate = True
                    if propagate:
                        self.solution[parent] = (parent_rem, parent_val)

    
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
