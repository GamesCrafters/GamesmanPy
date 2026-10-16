

from kaninariebi import KaniNariEbi
from models import StringMode

variants = ("regular", "mixed", "3x5", "5x3")

for variant in variants:
    game = KaniNariEbi(variant)
    start = game.start()

    # Test 1: String round-trip
    encoded = game.to_string(start, StringMode.Readable)
    restored = game.from_string(encoded)

    assert restored == start

    expected_row = (
        "C" + "-" * (game._COLS - 2) + "c"
    )
    expected = "1_" + expected_row * game._ROWS

    assert encoded == expected, (
        f"{variant}: expected {expected}, got {encoded}"
    )

    # Test 2: Complete legal moves
    moves = game.generate_moves(start)

    for move in moves:
        next_pos = game.do_move(start, move)
        next_str = game.to_string(
            next_pos, StringMode.Readable
        )
        assert game.from_string(next_str) == next_pos

    # Test 3: Group moves by AutoGUI arrow
    groups = game._group_web_moves(start)

    assert sum(len(g) for g in groups.values()) == len(moves)

    ambiguous = {
        key: group
        for key, group in groups.items()
        if len(group) > 1
    }


    # Test 4: Every complete move must have a unique choice path
    paths = [
        game._web_move_steps(start, move)
        for move in moves
    ]

    assert len(paths) == len(set(paths)), (
        f"{variant}: Multiple moves share the same Web choices"
    )

    print(f"Unique Web move paths: {len(paths)}")


    print(f"\nVariant: {variant}")
    print(f"Position: {encoded}")
    print(f"Legal moves: {len(moves)}")
    print(f"Unique arrows: {len(groups)}")
    print(f"Arrows with multiple outcomes: {len(ambiguous)}")

    for (src, dest), group in list(ambiguous.items())[:3]:
        print(f"  M_{src}_{dest}_x -> {len(group)} choices")

    print("PASS")

print("\nAll tests passed!")
