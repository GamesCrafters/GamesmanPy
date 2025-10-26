from solver.src.acyclic import AcyclicSolver
from database.database import PuzzleDB

class TUI:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        solver = AcyclicSolver(self.puzzle)
        solver.solve()
        