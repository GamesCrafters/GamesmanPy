
from kaninariebi import KaniNariEbi
from models import StringMode

for variant in ("regular", "mixed", "3x5", "5x3"):
    game = KaniNariEbi(variant)
    start = game.start()

    # Test the number of AutoGUI centers.
    position_str = game.to_string(start, StringMode.AUTOGUI)
    turn, cells = position_str.split("_", 1)

    assert turn == "1"
    assert len(cells) == game._BOARD_SIZE + 5
    assert cells.endswith("-----")

    # Test the five action buttons.
    n = game._BOARD_SIZE

    expected = {
        ("current", game._CURRENT_UP): f"T_UP_{n}_-",
        ("current", game._CURRENT_DOWN): f"T_DOWN_{n+1}_-",
        ("promote", 1): f"T_YES_{n+2}_-",
        ("promote", 0): f"T_NO_{n+3}_-",
        ("end",): f"T_END_{n+4}_-",
    }

    for choice, output in expected.items():
        actual = game.move_to_string(choice, StringMode.AUTOGUI)
        assert actual == output, (choice, actual, output)

    # Test every available half-move from the opening.
    count = 0

    for full_move in game.generate_moves(start):
        state = start

        for choice in game._web_move_steps(start, full_move):
            assert choice in game.generate_half_moves(state)

            button = game.move_to_string(
                choice, StringMode.AUTOGUI
            )

            assert button.startswith(("M_", "T_"))
            assert len(button.split("_")) == 4

            state, _, _, _ = game.do_half_move(state, choice)
            count += 1

            if isinstance(state, int):
                break

    print(f"{variant}: PASS ({count} actions tested)")

print("All AutoGUI button tests passed!")

