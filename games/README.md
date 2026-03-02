# Adding a Game/Puzzle

Make a copy of `games/src/games/example.py` and rename. Update class name, variants, `n_players`, etc. to match.

Import the new class in `games/src/games/game_manager.py`, and add to `game_list`.

Required functions:
* `__init__` : should be mostly done for you, just update class name and create additional instance variables if needed.
* `start` : returns the starting position of the game, as an integer.
* `generate_moves` : returns a list of valid moves from the given (integer) position. Moves should also be encoded as integers.
* `do_move` : applies the given move to the given position, and returns the resulting position as an integer.
* `primitive` : returns the value (`Value.Loss`, `Value.Tie`, `Value.Win`) of a position if it is primitive, else returns `None`.
* `to_string` : transform and return the given integer position into a string representation, based on the given mode.
* `from_string` : transform and return the given `StringMode.Readable` position string into the integer representation.
* `move_to_string` : transform and return the given integer move into a string representation, based on the given mode.

Recommended functions:
* `hash` : used to transform an internal, readable representation of a position into an integer in a reversible way. You can design this as you see fit. May be unnecessary for games/puzzles that have an obvious integer state representation (i.e. ten-to-zero).
* `unhash` : reverse of hash.

Run `uv run solver <your_game_name>` to solve all variants, or add `-v <variant_name>` for specific variants. To overwrite an existing database and resolve, add `-o`.
