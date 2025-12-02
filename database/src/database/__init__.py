from .database import GameDB
from .duckdb_database import DuckDB
from .sqlite_database import SqliteDB

def main() -> None:
    print("Hello from database!")
