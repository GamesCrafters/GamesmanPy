"""
Tiered solver for Fjords.

Every Fjords move colors exactly one vertex, so a position after k moves (tier k) only leads to
positions after k + 1 moves. That lets the game be solved one tier at a time with only two tiers
in memory:

  Pass 1 (forward):  tier k+1 = all children of tier k, sorted and saved to disk.
  Pass 2 (backward): solve tier k by looking up its children's results in tier k+1.

Positions use the same integers as games.fjords.Fjords (2 bits per initially-uncolored vertex,
digit 0 in the low bits), and results are written to the same SQLite table the regular solver
writes, so the server, TUI and GUI read them unchanged.

Usage:
    uv run python -m solver.fjords_tiered <variant> [--count-only] [--db PATH] [--keep-tiers]
"""
import argparse
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

import numpy as np

from games.fjords import Fjords
from models import Value

LOSS = np.uint8(int(Value.Loss))
WIN = np.uint8(int(Value.Win))
CHUNK = 2_000_000
DB_BYTES_PER_POSITION = 16  # measured ~15 B/position for GamesmanPy's SQLite table
MIN_FREE_BYTES = 1_000_000_000


class TieredFjordsSolver:
    def __init__(self, board, mutable_indices):
        self.n_digits = len(mutable_indices)
        if 2 * self.n_digits > 64:
            raise ValueError("positions must fit in 64 bits (at most 32 open vertices)")
        digit_of = {v: d for d, v in enumerate(mutable_indices)}
        # For every digit (open vertex): its neighbors, split into seeds (fixed color) and digits.
        self.seed_neighbor_colors = []
        self.digit_neighbors = []
        for v in mutable_indices:
            neighbors = board[v][1]
            self.seed_neighbor_colors.append({board[u][0] for u in neighbors if u not in digit_of})
            self.digit_neighbors.append([digit_of[u] for u in neighbors if u in digit_of])

    def _children(self, positions, mover):
        """Yield (digit, mask, children) for each digit: which positions may color it, and the results."""
        states = [((positions >> np.uint64(2 * d)) & np.uint64(3)).astype(np.uint8) for d in range(self.n_digits)]
        owns = [s == mover for s in states]
        for d in range(self.n_digits):
            if mover in self.seed_neighbor_colors[d]:
                legal = states[d] == 0
            else:
                adjacent = np.zeros(len(positions), dtype=bool)
                for u in self.digit_neighbors[d]:
                    adjacent |= owns[u]
                legal = (states[d] == 0) & adjacent
            if legal.any():
                yield d, legal, positions[legal] | np.uint64(mover << (2 * d))

    @staticmethod
    def _mover(tier):
        return 1 if tier % 2 == 0 else 2  # Blue moves first

    def discover(self, work_dir, log):
        """Pass 1: write every tier's sorted positions to work_dir; return the tier sizes."""
        tier, current = 0, np.zeros(1, dtype=np.uint64)  # start position is 0
        sizes = []
        while len(current):
            if shutil.disk_usage(work_dir).free - current.nbytes < MIN_FREE_BYTES:
                raise SystemExit(f"Stopping in pass 1: tier {tier} ({len(current):,} positions) "
                                 f"would leave less than {MIN_FREE_BYTES / 1e9:.0f} GB of free disk.")
            np.save(work_dir / f"tier{tier}.npy", current)
            sizes.append(len(current))
            log(f"  tier {tier:>2}: {len(current):>13,} positions")
            pieces = []
            for start in range(0, len(current), CHUNK):
                chunk = current[start:start + CHUNK]
                kids = [c for _, _, c in self._children(chunk, self._mover(tier))]
                if kids:
                    pieces.append(np.unique(np.concatenate(kids)))
            current = np.unique(np.concatenate(pieces)) if pieces else np.zeros(0, dtype=np.uint64)
            tier += 1
        return sizes

    def solve_tiers(self, work_dir, n_tiers, write, keep_tiers, log):
        """Pass 2: solve from the last tier back to tier 0, handing each solved tier to write()."""
        next_keys = np.zeros(0, dtype=np.uint64)
        next_value = np.zeros(0, dtype=np.uint8)
        next_rem = np.zeros(0, dtype=np.uint16)
        for tier in range(n_tiers - 1, -1, -1):
            keys = np.load(work_dir / f"tier{tier}.npy")
            value = np.empty(len(keys), dtype=np.uint8)
            rem = np.empty(len(keys), dtype=np.uint16)
            for start in range(0, len(keys), CHUNK):
                chunk = keys[start:start + CHUNK]
                n = len(chunk)
                has_child = np.zeros(n, dtype=bool)
                has_losing_child = np.zeros(n, dtype=bool)
                min_losing_rem = np.full(n, np.iinfo(np.uint16).max, dtype=np.uint16)
                max_rem = np.zeros(n, dtype=np.uint16)
                for _, legal, kids in self._children(chunk, self._mover(tier)):
                    rows = np.flatnonzero(legal)
                    idx = np.searchsorted(next_keys, kids)
                    if (idx >= len(next_keys)).any() or (next_keys[np.minimum(idx, len(next_keys) - 1)] != kids).any():
                        raise RuntimeError(f"tier {tier}: a child is missing from tier {tier + 1}")
                    kid_value, kid_rem = next_value[idx], next_rem[idx]
                    has_child[rows] = True
                    losing = kid_value == LOSS
                    has_losing_child[rows[losing]] = True
                    np.minimum.at(min_losing_rem, rows[losing], kid_rem[losing])
                    np.maximum.at(max_rem, rows, kid_rem)
                # No moves: the player to move loses (Fjords.primitive). Otherwise win if some
                # move leaves the opponent lost (quickest such win), else lose (slowest loss).
                v = np.where(has_losing_child, WIN, LOSS).astype(np.uint8)
                r = np.where(has_losing_child, min_losing_rem + 1, max_rem + 1).astype(np.uint16)
                r[~has_child] = 0
                value[start:start + n], rem[start:start + n] = v, r
            write(keys, rem, value)
            wins = int((value == WIN).sum())
            log(f"  tier {tier:>2}: {len(keys):>13,} solved ({wins:,} wins, {len(keys) - wins:,} losses)")
            if not keep_tiers:
                (work_dir / f"tier{tier}.npy").unlink()
            next_keys, next_value, next_rem = keys, value, rem
        return int(next_value[0]), int(next_rem[0])


def default_db_path(variant):
    import database.sqlite_database as sqlite_database
    return Path(sqlite_database.__file__).resolve().parents[2] / "db" / f"{Fjords.id}_{variant}.db"


def open_db(path):
    if path.exists():
        path.unlink()
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode = OFF")
    db.execute("PRAGMA synchronous = OFF")
    # Same schema as database.SqliteDB.create_table.
    db.execute("CREATE TABLE gamedb (state INTEGER PRIMARY KEY, remoteness INTEGER, value INTEGER)")
    return db


def main():
    parser = argparse.ArgumentParser(description="Tiered solver for Fjords")
    parser.add_argument("variant", help="Fjords variant id, e.g. regular or random12")
    parser.add_argument("--count-only", action="store_true", help="only run pass 1 and report tier sizes")
    parser.add_argument("--db", type=Path, default=None, help="output database path (default: GamesmanPy's db file)")
    parser.add_argument("--keep-tiers", action="store_true", help="keep the per-tier files after solving")
    args = parser.parse_args()

    game = Fjords(args.variant)
    solver = TieredFjordsSolver(game.board, game._mutable_indices)
    db_path = args.db or default_db_path(args.variant)

    def log(msg):
        print(msg, flush=True)

    work_dir = Path(tempfile.mkdtemp(prefix=f"fjords_tiers_{args.variant}_", dir=db_path.parent))
    try:
        log(f"Fjords {args.variant}: {solver.n_digits} open vertices")
        log("Pass 1: discovering positions tier by tier")
        t0 = time.perf_counter()
        sizes = solver.discover(work_dir, log)
        total = sum(sizes)
        log(f"Pass 1 done: {total:,} positions in {len(sizes)} tiers, biggest tier {max(sizes):,} "
            f"({time.perf_counter() - t0:.1f}s)")
        if args.count_only:
            return

        needed = total * DB_BYTES_PER_POSITION
        free = shutil.disk_usage(db_path.parent).free
        log(f"Database needs about {needed / 1e9:.2f} GB; {free / 1e9:.2f} GB free")
        if needed > free:
            log("Not enough free disk space; stopping before pass 2.")
            raise SystemExit(1)

        db = open_db(db_path)

        def write(keys, rem, value):
            db.executemany("INSERT INTO gamedb VALUES (?, ?, ?)",
                           zip(keys.tolist(), rem.tolist(), value.tolist()))
            db.commit()

        log("Pass 2: solving tiers from the end of the game back to the start")
        t1 = time.perf_counter()
        start_value, start_rem = solver.solve_tiers(work_dir, len(sizes), write, args.keep_tiers, log)
        db.close()
        log(f"Pass 2 done ({time.perf_counter() - t1:.1f}s). Start position: "
            f"{Value(start_value).name} in {start_rem} moves")
        log(f"Wrote {total:,} positions to {db_path} ({os.path.getsize(db_path) / 1e6:.1f} MB)")
    finally:
        if not args.keep_tiers:
            shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
