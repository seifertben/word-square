"""End-to-end board generation pipeline.

Build a 6x6 double word grid and blank out a fraction of its cells; the player
fills them back in. Lines may run in either direction and may contain five
letters when their sixth cell is blocked on the perimeter. The
completed square ships as the hidden solution (powering Reveal), while real win
validation is open-ended against the dictionary.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
from pathlib import Path
from zoneinfo import ZoneInfo

from generator.dictionary import Dictionary, get_dictionary, write_trimmed_json
from generator.models import GRID_SIZE, Board
from generator.store import BoardStore, get_store
from generator.word_square import build_square

_OUTER_KEEP_RATIO = 0.6
_INNER_BLANK_RATIO = 0.5

_ET = ZoneInfo("America/New_York")


def _defaults() -> tuple[int, float, float]:
    import os

    size = int(os.environ.get("BOARD_SIZE", GRID_SIZE))
    outer_keep = float(os.environ.get("OUTER_KEEP_RATIO", _OUTER_KEEP_RATIO))
    inner_blank = float(os.environ.get("INNER_BLANK_RATIO", _INNER_BLANK_RATIO))
    return size, outer_keep, inner_blank


def _date_seed(date: str) -> int:
    y, m, d = (int(x) for x in date.split("-"))
    return y * 10000 + m * 100 + d


def _pick_blanks(
    size: int,
    rng: random.Random,
    blocked: set[tuple[int, int]] | None = None,
    *,
    outer_keep_ratio: float = _OUTER_KEEP_RATIO,
    inner_blank_ratio: float = _INNER_BLANK_RATIO,
) -> set[tuple[int, int]]:
    blocked = blocked or set()
    cells = [(r, c) for r in range(size) for c in range(size) if (r, c) not in blocked]
    outer = [(r, c) for r, c in cells if r in (0, size - 1) or c in (0, size - 1)]
    inner = [(r, c) for r, c in cells if (r, c) not in outer]

    # Keep ``outer_keep_ratio`` of the ring letters and blank ``inner_blank_ratio``
    # of the middle.
    rng.shuffle(outer)
    rng.shuffle(inner)
    blanks = set(outer[round(len(outer) * outer_keep_ratio) :])
    blanks.update(inner[: round(len(inner) * inner_blank_ratio)])

    # Keep every row and column anchored with at least one given letter so no
    # line is left entirely to guess.
    for _ in range(size):
        changed = False
        for r in range(size):
            active = [(r, c) for c in range(size) if (r, c) not in blocked]
            if all(cell in blanks for cell in active):
                blanks.remove(rng.choice(active))
                changed = True
        for c in range(size):
            active = [(r, c) for r in range(size) if (r, c) not in blocked]
            if all(cell in blanks for cell in active):
                blanks.remove(rng.choice(active))
                changed = True
        if not changed:
            break
    return blanks


def generate_board(
    date: str | None = None,
    *,
    seed: int | None = None,
    size: int | None = None,
    outer_keep_ratio: float | None = None,
    inner_blank_ratio: float | None = None,
    dictionary: Dictionary | None = None,
    recent_squares: list[list[str]] | None = None,
) -> Board:
    """Generate and return a solvable 6x6 word-square board for ``date``.

    Roughly ``outer_keep_ratio`` of the outer-ring cells are kept as givens
    while ``inner_blank_ratio`` of the interior cells are blanked; the player
    fills them so that every row and column is a dictionary word.
    """
    d_size, d_outer_keep, d_inner_blank = _defaults()
    size = size if size is not None else d_size
    outer_keep = outer_keep_ratio if outer_keep_ratio is not None else d_outer_keep
    inner_blank = inner_blank_ratio if inner_blank_ratio is not None else d_inner_blank

    date = date or dt.datetime.now(_ET).date().strftime("%Y-%m-%d")
    seed = seed if seed is not None else _date_seed(date)
    dictionary = dictionary or get_dictionary(min_len=size - 1, max_len=size)

    rows = build_square(
        dictionary,
        seed=seed,
        recent_squares=recent_squares,
    )

    return board_from_solution(
        rows,
        date=date,
        seed=seed,
        outer_keep_ratio=outer_keep,
        inner_blank_ratio=inner_blank,
    )


def board_from_solution(
    rows: list[str],
    *,
    date: str,
    seed: int | None = None,
    outer_keep_ratio: float | None = None,
    inner_blank_ratio: float | None = None,
) -> Board:
    """Materialize a playable board from a pre-generated square."""
    size = len(rows)
    if size == 0 or any(len(row) != size for row in rows):
        raise ValueError("solution must be a non-empty square")

    _, d_outer_keep, d_inner_blank = _defaults()
    outer_keep = outer_keep_ratio if outer_keep_ratio is not None else d_outer_keep
    inner_blank = inner_blank_ratio if inner_blank_ratio is not None else d_inner_blank
    board_seed = seed if seed is not None else _date_seed(date)
    rng = random.Random(board_seed ^ 0x9E3779B9)
    blocked = {(r, c) for r in range(size) for c in range(size) if rows[r][c] == "#"}
    if any(r not in (0, size - 1) and c not in (0, size - 1) for r, c in blocked):
        raise ValueError("blocked cells must be on the outer ring")
    blanks = _pick_blanks(
        size,
        rng,
        blocked,
        outer_keep_ratio=outer_keep,
        inner_blank_ratio=inner_blank,
    )
    fixed = {
        (r, c): rows[r][c]
        for r in range(size)
        for c in range(size)
        if (r, c) not in blanks and (r, c) not in blocked
    }

    return Board(
        size=size,
        min_word_length=size - 1,
        fixed=fixed,
        blocked=blocked,
        solution=list(rows),
        date=date,
    )


def emit_dictionary_asset(dictionary: Dictionary, out_path: str | Path) -> int:
    """Write the trimmed word list for the client bundle."""
    return write_trimmed_json(out_path, dictionary)


def _recent_solutions(store: BoardStore, before: str, *, limit: int = 30) -> list[list[str]]:
    """Load valid prior solutions so generation can avoid recent vocabulary."""
    solutions: list[list[str]] = []
    dates = [date for date in store.list_dates() if date < before][-limit:]
    for date in dates:
        payload = store.get(date)
        if payload is None:
            continue
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        solution = data.get("solution")
        if not isinstance(solution, list):
            continue
        rows = [word for word in solution if isinstance(word, str)]
        if len(rows) == GRID_SIZE and all(len(word) == GRID_SIZE for word in rows):
            solutions.append(rows)
    return solutions


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    parser = argparse.ArgumentParser(description="Generate one daily word-square board.")
    parser.add_argument("date", nargs="?", help="YYYY-MM-DD (default: today ET)")
    parser.add_argument("--seed", type=int, help="override the date-derived seed")
    parser.add_argument("--size", type=int, default=None)
    parser.add_argument("--outer-keep-ratio", type=float, default=None)
    parser.add_argument("--inner-blank-ratio", type=float, default=None)
    parser.add_argument(
        "--dictionary-out",
        type=str,
        default=None,
        help="path to write the trimmed client dictionary JSON (default: none)",
    )
    args = parser.parse_args()

    date = args.date or dt.datetime.now(_ET).date().strftime("%Y-%m-%d")
    store = get_store()
    board = generate_board(
        date,
        seed=args.seed,
        size=args.size,
        outer_keep_ratio=args.outer_keep_ratio,
        inner_blank_ratio=args.inner_blank_ratio,
        recent_squares=_recent_solutions(store, date),
    )

    from generator.serialize import board_to_json

    payload = board_to_json(board)
    assert board.date is not None
    store.put(board.date, payload)
    n_fixed = len(board.fixed)
    n_blank = board.size * board.size - n_fixed
    print(
        f"Generated {board.date}: {board.size}x{board.size} word square "
        f"({n_fixed} given, {n_blank} blank cells)"
    )
    if args.dictionary_out:
        dictionary = get_dictionary(min_len=board.min_word_length, max_len=board.size)
        n = emit_dictionary_asset(dictionary, args.dictionary_out)
        print(f"Wrote {n} words to {args.dictionary_out}")


if __name__ == "__main__":
    main()
