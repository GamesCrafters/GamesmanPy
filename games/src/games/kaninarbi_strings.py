
from kaninariebi import KaniNariEbi
from models import StringMode

for variant in ("regular", "mixed", "3x5"):
    game = KaniNariEbi(variant)

    position = game.start()

    encoded = game.to_string(position, StringMode.Readable)
    restored = game.from_string(encoded)

    print(f"Variant: {variant}")
    print(f"Encoded: {encoded}")
    print(f"Round-trip test: {'PASS' if position == restored else 'FAIL'}")
    print()

    expected_rows = 3 if variant == "3x5" else 5
    expected = "1_" + "C---c" * expected_rows

    assert encoded == expected, (f"Expected {expected}, got {encoded}")
    
    assert position == restored

print("All tests passed!")
