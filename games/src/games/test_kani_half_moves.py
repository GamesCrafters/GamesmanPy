
from kaninariebi import KaniNariEbi

variants = ("regular", "mixed", "3x5", "5x3")

for variant in variants:
    game = KaniNariEbi(variant)
    start = game.start()
    full_moves = game.generate_moves(start)

    print(f"\nTesting {variant}...")
    checked = 0

    for full_move in full_moves:
        expected = game.do_move(start, full_move)
        steps = game._web_move_steps(start, full_move)

        state = start

        for choice in steps:
            available = game.generate_half_moves(state)

            assert choice in available, (
                f"{variant}: Missing choice {choice}"
            )

            state, _, _, _ = game.do_half_move(
                state, choice
            )

            # The turn may finish before all choices have
            # been visited if only one legal move remains.
            if isinstance(state, int):
                break

        assert isinstance(state, int), (
            f"{variant}: Did not finish the turn"
        )

        assert state == expected, (
            f"{variant}: Half move result differs "
            f"from the original do_move"
        )

        checked += 1

    print(f"Verified {checked} complete moves: PASS")

print("\nAll half-move tests passed!")
