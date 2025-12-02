# GamesmanPy

GamesmanPy is designed to be an entry point into the GamesCrafters game and puzzle
solving systems. It can solve relatively small (~10 million positions) games and
puzzles and has a server module that allows GamesmanPy to interface with
[GamesCraftersUWAPI](https://github.com/GamesCrafters/GamesCraftersUWAPI).

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

To give an idea of the capabilities of GamesmanPy, here are some example solve
times of various sized games.

| Number of States | Solve Time |
|------------------|------------|
| 3,840            | 0.06s      |
| 46,080           | 0.95s      |
| 645,120          | 19.20s     |
| 10,321,920       | 412.99s    |

For games much larger than this, you may want to look into some of our more
performant systems, like
[GamesmanClassic](https://github.com/GamesCrafters/GamesmanClassic),
[GamesmanOne](https://github.com/GamesCrafters/GamesmanOne), or
[GamesmanNova](https://github.com/GamesCrafters/GamesmanNova).