#GamesmanPy

GamesmanPy is designed to be an entry point into the GamesCrafters game and puzzle
solving systems. It can solve relatively small (~10 million positions) games and
puzzles and has a server module which will serve the games to the GamesmanUni
backend, GamesCraftersUWAPI.

To install GamesmanPy, follow these steps:
1. Clone the repository with `git clone git@github.com:GamesCrafters/GamesmanPy.git`
2. Install [astral uv](https://github.com/astral-sh/uv)
3. Inside the GamesmanPy folder, run `uv sync`

You are now ready to use GamesmanPy.
To run the solver, use `uv run solver <game_id>`, or if you want to solve
everything, `uv run solver` (this might take a while). You can also use `-v <variant_id>`
to solve a specific variant of the game, and `-o` to overwrite the existing database,
if it exists.

To run the server, use `uv run server`. This will start a local server on port 9004.

To run the tui, use `uv run interfaces tui`. This will open up a text user interface
where you can play the games in the system.