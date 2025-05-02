from solver.acyclic import AcyclicSolver
from games.ten_to_zero import TenToZero

t = TenToZero()
s = AcyclicSolver(t)
s.solve(overwrite=True)
s.print()