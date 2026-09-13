"""English dictionary loader (ESDB word list) + client-bundle trimmer.

The source list is ``data/words.txt`` (English Speller Database), one word per
line. The generator reads it directly; a trimmed, gzipped-friendly JSON asset
is emitted for the browser so validation can run fully client-side.

Only alphabetic A-Z words of length ``min_len..max_len`` are kept.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

_DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "words.txt"
DEFAULT_MIN_LEN = 3
DEFAULT_MAX_LEN = 9


def _read_words(path: Path) -> set[str]:
    words: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            token = line.strip().upper()
            if token and not token.startswith("#") and token.isalpha():
                words.add(token)
    return words


class Dictionary:
    """A set of valid English words, indexed by length for fast lookups."""

    def __init__(self, words: set[str], *, min_len: int, max_len: int) -> None:
        self.min_len = min_len
        self.max_len = max_len
        self._words: frozenset[str] = frozenset(w for w in words if min_len <= len(w) <= max_len)
        by_length: dict[int, set[str]] = {}
        index: dict[tuple[int, int, str], set[str]] = {}
        for w in self._words:
            by_length.setdefault(len(w), set()).add(w)
            for pos, ch in enumerate(w):
                index.setdefault((len(w), pos, ch), set()).add(w)
        self._by_length = {k: frozenset(v) for k, v in by_length.items()}
        self._by_len_pos_letter = {k: tuple(v) for k, v in index.items()}

    def contains(self, word: str) -> bool:
        return word.upper() in self._words

    def words_of_length(self, length: int) -> frozenset[str]:
        return self._by_length.get(length, frozenset())

    def words_with_letter_at(self, length: int, pos: int, letter: str) -> tuple[str, ...]:
        """All words with ``letter`` at index ``pos`` (0-based), by length."""
        return self._by_len_pos_letter.get((length, pos, letter), ())

    def has_length(self, length: int) -> bool:
        return length in self._by_length

    def lengths(self) -> list[int]:
        return sorted(self._by_length)

    def __len__(self) -> int:
        return len(self._words)

    def __contains__(self, word: str) -> bool:
        return self.contains(word)


@lru_cache(maxsize=1)
def get_dictionary(
    path: str | os.PathLike[str] | None = None,
    *,
    min_len: int | None = None,
    max_len: int | None = None,
) -> Dictionary:
    """Load (and cache) the default dictionary from the data directory."""
    p = Path(path) if path else _DEFAULT_PATH
    if min_len is None:
        min_len = DEFAULT_MIN_LEN
    if max_len is None:
        max_len = DEFAULT_MAX_LEN
    return Dictionary(_read_words(p), min_len=min_len, max_len=max_len)


def words_as_payload(
    dictionary: Dictionary,
) -> list[str]:
    """The trimmed word list as a sorted Python list, ready for JSON output."""
    return sorted(dictionary._words)


def write_trimmed_json(
    out_path: str | os.PathLike[str],
    dictionary: Dictionary,
) -> int:
    """Write the trimmed word list as a JSON array file (one level, gzip-friendly)."""
    payload = words_as_payload(dictionary)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return len(payload)


def reset_cache() -> None:
    get_dictionary.cache_clear()
