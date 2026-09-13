"""Seeded 6x6 double word-grid generation."""

from __future__ import annotations

import random
import time

from wordfreq import zipf_frequency

from generator.dictionary import Dictionary

N = 6
BLOCK = "#"
_NODES_PER_ATTEMPT = 300_000
_MAX_ATTEMPTS = 16
_MAX_ATTEMPTS_WITH_HISTORY = 64
_MAX_FALLBACK_OVERLAP = 11
_TARGET_FILLS = 8


class WordSquareError(Exception):
    """Raised when no double word grid can be built within the time limit."""


def _canonical_word(word: str) -> str:
    return min(word, word[::-1])


def _ordered_words(dictionary: Dictionary, seed: int) -> list[str]:
    words: set[str] = set()
    for length in (N - 1, N):
        for word in dictionary.words_of_length(length):
            words.add(word)
            words.add(word[::-1])
    ordered = sorted(words)
    random.Random(seed).shuffle(ordered)
    return ordered


def _seeded_order(words: list[str], seed: int) -> list[str]:
    """Vary search order without changing a pool's membership."""
    rng = random.Random(seed)
    ordered = list(words)
    for start in range(0, len(ordered), 32):
        block = ordered[start : start + 32]
        rng.shuffle(block)
        ordered[start : start + 32] = block
    return ordered


def _transpose(square: list[str]) -> list[str]:
    return ["".join(square[row][column] for row in range(N)) for column in range(N)]


def _columns(square: list[str]) -> list[str]:
    return [word.replace(BLOCK, "") for word in _transpose(square)]


def _rows(square: list[str]) -> list[str]:
    return [word.replace(BLOCK, "") for word in square]


def _word_set(square: list[str]) -> set[str]:
    return set(_rows(square)) | set(_columns(square))


def _word_familiarity(word: str) -> float:
    """Return the stronger English frequency for either reading direction."""
    return max(zipf_frequency(word, "en"), zipf_frequency(word[::-1], "en"))


def _familiarity(square: list[str]) -> tuple[float, ...]:
    """Rank a fill by its weakest words first."""
    return tuple(sorted(_word_familiarity(word) for word in _word_set(square)))


def _square_key(square: list[str]) -> tuple[str, ...]:
    return min(tuple(square), tuple(_transpose(square)))


def _select_square(
    candidates: list[list[str]],
    *,
    seed: int,
    recent_squares: list[list[str]],
) -> list[str]:
    """Select a fill with familiar vocabulary and minimal vocabulary reuse."""
    recent_words = [_word_set(square) for square in recent_squares]

    def novelty(square: list[str]) -> tuple[int, int]:
        words = _word_set(square)
        overlaps = [len(words & previous) for previous in recent_words]
        return (max(overlaps, default=0), sum(overlaps))

    def ranking(square: list[str]) -> tuple[tuple[float, ...], tuple[int, int], tuple[str, ...]]:
        return (
            tuple(-score for score in _familiarity(square)),
            novelty(square),
            tuple(square),
        )

    square = list(sorted(candidates, key=ranking)[0])
    if seed % 2:
        return _transpose(square)
    return square


def _block_pattern(seed: int) -> set[tuple[int, int]]:
    """Choose opposite corners, producing four contiguous five-letter words."""
    diagonals = [
        {(0, 0), (N - 1, N - 1)},
        {(0, N - 1), (N - 1, 0)},
    ]
    return diagonals[seed % len(diagonals)]


def _solve_pool(
    pool: list[str],
    *,
    seed: int,
    deadline: float,
    node_limit: int,
    excluded: set[tuple[str, ...]],
    avoided_words: set[str],
    solution_limit: int,
    blocked: set[tuple[int, int]] | None = None,
) -> tuple[list[list[str]], list[list[str]]]:
    words = _seeded_order(pool, seed)
    blocked = blocked or set()
    words_by_length = {
        length: [word for word in words if len(word) == length] for length in (N - 1, N)
    }

    row_options: list[list[str]] = []
    row_position_bits: list[dict[tuple[int, str], int]] = []
    for row in range(N):
        blocked_columns = [column for column in range(N) if (row, column) in blocked]
        length = N - len(blocked_columns)
        options: list[str] = []
        for word in words_by_length[length]:
            chars = iter(word)
            options.append(
                "".join(BLOCK if column in blocked_columns else next(chars) for column in range(N))
            )
        row_options.append(options)
        position_bits: dict[tuple[int, str], int] = {}
        for index, placement in enumerate(options):
            bit = 1 << index
            for column, letter in enumerate(placement):
                if letter != BLOCK:
                    key = column, letter
                    position_bits[key] = position_bits.get(key, 0) | bit
        row_position_bits.append(position_bits)

    # Letters which can extend each prefix of a possible down word.
    next_letters: dict[tuple[int, str], int] = {}
    for length, length_words in words_by_length.items():
        for word in length_words:
            for prefix_length, letter in enumerate(word):
                key = length, word[:prefix_length]
                next_letters[key] = next_letters.get(key, 0) | (1 << (ord(letter) - 65))

    column_lengths = [N - sum((row, column) in blocked for row in range(N)) for column in range(N)]
    rows: list[str] = []
    prefixes = [""] * N
    used_words: set[str] = set()
    nodes = 0
    solutions: dict[tuple[str, ...], list[str]] = {}
    fallback_solutions: dict[tuple[str, ...], list[str]] = {}

    def search() -> bool:
        nonlocal nodes
        nodes += 1
        if nodes > node_limit or (nodes & 0xFFF == 0 and time.monotonic() >= deadline):
            return True

        depth = len(rows)
        if depth == N:
            row_words = _rows(rows)
            columns = list(prefixes)
            canonical_rows = {_canonical_word(word) for word in row_words}
            canonical_columns = {_canonical_word(word) for word in columns}
            if len(canonical_rows) < N or len(canonical_columns) < N:
                return False
            if canonical_rows & canonical_columns:
                return False
            key = _square_key(rows)
            if key not in excluded:
                destination = (
                    fallback_solutions
                    if (set(row_words) | set(columns)) & avoided_words
                    else solutions
                )
                destination.setdefault(key, list(rows))
            return len(solutions) >= solution_limit

        options = row_options[depth]
        candidates = (1 << len(options)) - 1
        for column in range(N):
            if (depth, column) in blocked:
                continue
            letters = next_letters.get((column_lengths[column], prefixes[column]), 0)
            matching = 0
            while letters:
                letter_bit = letters & -letters
                letters ^= letter_bit
                letter = chr(letter_bit.bit_length() - 1 + 65)
                matching |= row_position_bits[depth].get((column, letter), 0)
            candidates &= matching
            if candidates == 0:
                return False

        while candidates:
            bit = candidates & -candidates
            candidates ^= bit
            placement = options[bit.bit_length() - 1]
            word = placement.replace(BLOCK, "")
            canonical = _canonical_word(word)
            if canonical in used_words:
                continue

            previous = list(prefixes)
            for column, letter in enumerate(placement):
                if letter != BLOCK:
                    prefixes[column] += letter
            rows.append(placement)
            used_words.add(canonical)
            stop = search()
            used_words.remove(canonical)
            rows.pop()
            prefixes[:] = previous
            if stop:
                return True
        return False

    search()
    return list(solutions.values()), list(fallback_solutions.values())


def build_square(
    dictionary: Dictionary,
    *,
    seed: int,
    max_seconds: float = 600.0,
    recent_squares: list[list[str]] | None = None,
) -> list[str]:
    """Build a deterministic 6x6 fill using five- and six-letter words.

    Words may run forward or backward. When five-letter words are available,
    opposite corners are blocked so two rows and two columns are five letters long.
    """
    if max_seconds <= 0:
        raise ValueError("max_seconds must be positive")
    if not dictionary.words_of_length(N):
        raise WordSquareError("the dictionary contains no six-letter words")

    deadline = time.monotonic() + max_seconds
    recent_squares = recent_squares or []
    recent_word_sets = [_word_set(square) for square in recent_squares]
    recent_words = set().union(*recent_word_sets) if recent_word_sets else set()
    candidates: dict[tuple[str, ...], list[str]] = {}
    fallback_candidates: dict[tuple[str, ...], list[str]] = {}
    attempt_limit = _MAX_ATTEMPTS_WITH_HISTORY if recent_words else _MAX_ATTEMPTS
    use_blocks = bool(dictionary.words_of_length(N - 1))

    for attempt in range(attempt_limit):
        if time.monotonic() >= deadline:
            break
        attempt_seed = seed + attempt * 1_000_003
        found, fallback = _solve_pool(
            _ordered_words(dictionary, attempt_seed),
            seed=attempt_seed,
            deadline=deadline,
            node_limit=_NODES_PER_ATTEMPT,
            excluded=set(candidates),
            avoided_words=recent_words,
            solution_limit=1,
            blocked=_block_pattern(attempt_seed) if use_blocks else set(),
        )
        for square in found:
            candidates[_square_key(square)] = square
        for square in fallback:
            words = _word_set(square)
            if all(len(words & recent) <= _MAX_FALLBACK_OVERLAP for recent in recent_word_sets):
                fallback_candidates[_square_key(square)] = square
        if len(candidates) >= _TARGET_FILLS:
            break

    available = candidates or fallback_candidates
    if available:
        return _select_square(list(available.values()), seed=seed, recent_squares=recent_squares)
    raise WordSquareError(f"no sufficiently novel 6x6 double word grid found for seed {seed}")
