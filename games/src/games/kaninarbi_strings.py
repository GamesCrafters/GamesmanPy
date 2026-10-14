
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

    assert position == restored

print("All tests passed!")
