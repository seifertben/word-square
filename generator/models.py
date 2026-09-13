"""Core data structures for the word-square generator."""

from __future__ import annotations

from dataclasses import dataclass

GRID_SIZE = 6


@dataclass
class Board:
    """A ``size``-by-``size`` double word square with a fraction of cells blanked.

    Every row and every column of the completed grid is a valid English word.
    ``fixed`` holds the given (non-blank) letters the player sees; ``solution``
    holds the six across-words that make up the full square (powers Reveal).
    """

    size: int
    min_word_length: int
    fixed: dict[tuple[int, int], str]
    """(row, col) -> given letter (locked, non-blank cell)."""
    blocked: set[tuple[int, int]]
    """Unplayable perimeter cells, represented by ``#`` in the solution."""
    solution: list[str]
    """The six across-words (each ``size`` letters) of the completed square."""
    date: str | None = None

    def is_fixed(self, r: int, c: int) -> bool:
        return (r, c) in self.fixed

    def fixed_letter(self, r: int, c: int) -> str | None:
        return self.fixed.get((r, c))
