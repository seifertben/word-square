"""Word-square validation.

A completed grid is *solved* when every row and every column is a valid English
word (all cells filled). This is canonical here and mirrored in TypeScript at
``web/src/validate.ts`` so generator/tests and the client agree.
"""

from __future__ import annotations

from typing import cast

from generator.dictionary import Dictionary

Grid = list[list[str | None]]


def is_complete(grid: Grid) -> bool:
    return all(grid[r][c] is not None for r in range(len(grid)) for c in range(len(grid)))


def _is_dictionary_word(word: str, dictionary: Dictionary) -> bool:
    return dictionary.contains(word) or dictionary.contains(word[::-1])


def is_word_square(grid: Grid, dictionary: Dictionary, min_len: int | None = None) -> bool:
    """True iff every row and column is a dictionary word (and grid is complete)."""
    size = len(grid)
    if any(len(row) != size for row in grid):
        return False
    if not is_complete(grid):
        return False
    for r in range(size):
        row_word = "".join(cast(str, grid[r][c]) for c in range(size) if grid[r][c] != "#")
        if (min_len is not None and len(row_word) < min_len) or not _is_dictionary_word(
            row_word, dictionary
        ):
            return False
    for c in range(size):
        col_word = "".join(cast(str, grid[r][c]) for r in range(size) if grid[r][c] != "#")
        if (min_len is not None and len(col_word) < min_len) or not _is_dictionary_word(
            col_word, dictionary
        ):
            return False
    return True


def invalid_cells(
    grid: Grid,
    dictionary: Dictionary,
    min_len: int,
) -> set[tuple[int, int]]:
    """Cells belonging to a fully-filled row/column that is not a dictionary word.

    Powers the client "Check" button: only complete lines are judged, so partial
    lines are never penalized.
    """
    size = len(grid)
    bad: set[tuple[int, int]] = set()
    for r in range(size):
        cells = [(r, c) for c in range(size) if grid[r][c] != "#"]
        if any(grid[r][c] is None for r, c in cells):
            continue
        word = "".join(cast(str, grid[r][c]) for r, c in cells)
        if len(word) < min_len or not _is_dictionary_word(word, dictionary):
            bad.update(cells)
    for c in range(size):
        cells = [(r, c) for r in range(size) if grid[r][c] != "#"]
        if any(grid[r][c] is None for r, c in cells):
            continue
        word = "".join(cast(str, grid[r][c]) for r, c in cells)
        if len(word) < min_len or not _is_dictionary_word(word, dictionary):
            bad.update(cells)
    return bad
