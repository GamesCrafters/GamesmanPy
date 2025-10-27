from collections import deque
from models import Game, Value
from database import GameDB

REMOTENESS_TERMINAL = 0

class AcyclicSolver:
    def __init__(self, game: Game):
        self.game = game
        self.solution = {}
        self.parent_map = {}

    def solve(self, overwrite=False):
        for variant in self.game.variants:
          self.db = GameDB(self.game.id, variant)
          if overwrite or not self.db.exists:
              self.db.create_table(overwrite)
              self.discover()
              print("discovered")
              self.propagate()
              print("solved")
              print(self.solution)
              self.db.insert(self.solution)

    def get_children(self, position):
        moves = self.game.generate_moves(position)
        return map(lambda m: self.game.do_move(position, m), moves)

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
            else:
                children = self.get_children(position)
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
            parent_rem, val = self.solution.get(position)
            parent_rem += 1
            parent_val: Value = self.parent_value(val)
            parents = self.parent_map.get(position, set())
            for parent in parents:
                parent_sol = self.solution.get(parent)
                if parent_sol is None:
                    self.solution[parent] = (parent_rem, parent_val)
                    q.appendleft(parent)
                elif parent_sol[1] < parent_val:
                    self.solution[parent] = (parent_rem, parent_val)

    
    def parent_value(self, val: Value) -> Value:
        if self.game.n_players == 1:
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
            print(f'state: {position} | remoteness: {rem} | value: {Value(value).name}')
    
    def get_remoteness(self, state: int) -> int:
        rem, _ = self.db.get(state)
        if rem is None:
            return -1
        return rem
