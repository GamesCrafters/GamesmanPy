from solver import AcyclicSolver
from games import game_list


for game in game_list.values():
  s = AcyclicSolver(game)
  s.solve(overwrite=False)