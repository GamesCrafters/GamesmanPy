from .tui import TUI
from games import getGame
from models import Result

def main() -> None:
    print("Hello from interfaces!")

t = TUI()

t.play(getGame("ttt-inf", "default").unwrap(), "default")