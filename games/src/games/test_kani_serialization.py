
from kaninariebi import KaniNariEbi
from models import StringMode

for variant in ("regular", "mixed", "3x5", "5x3"):
    game = KaniNariEbi(variant)
    start = game.start()

    tested_states = 0

    for move in game.generate_moves(start):
        state = start
        steps = game._web_move_steps(start, move)

        for choice in steps:
            state, _, _, _ = game.do_half_move(state, choice)

            if isinstance(state, int):
                break

            readable = game.to_string(
                state, StringMode.Readable
            )
            restored = game.from_string(readable)

            assert restored == state
            assert game.hash_ext(state) == start

            autogui = game.to_string(
                state, StringMode.AUTOGUI
            )

            turn, chars = autogui.split("_", 1)

            assert turn == "1"
            assert len(chars) == game._BOARD_SIZE

            assert game.generate_half_moves(
                restored
            ) == game.generate_half_moves(state)

            tested_states += 1

    print(
        f"{variant}: PASS "
        f"({tested_states} intermediate states tested)"
    )

print("All serialization tests passed!")

