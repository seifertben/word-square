"""Offline tests for the word-square generator (no cloud required)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import generator.word_square as word_square
from generator.dictionary import Dictionary, get_dictionary, words_as_payload
from generator.models import GRID_SIZE
from generator.pipeline import _recent_solutions, board_from_solution, generate_board
from generator.store import LocalStore
from generator.validate import is_word_square
from generator.word_square import _select_square, build_square


def _dict() -> Dictionary:
    return get_dictionary(min_len=GRID_SIZE, max_len=GRID_SIZE)


def _solution_grid(rows: list[str]) -> list[list[str | None]]:
    return [[ch for ch in row] for row in rows]


def test_dictionary_trims_to_length_range() -> None:
    d = get_dictionary(min_len=6, max_len=6)
    assert d.min_len == 6
    assert d.max_len == 6
    assert d.contains("LADDER")
    assert not d.contains("WORD")  # wrong length
    assert all(len(w) == 6 for w in words_as_payload(d))


def test_validation_accepts_words_written_backwards() -> None:
    rows = ["SECALP", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"]
    words = {"PLACES", *rows[1:]}
    words.update(
        "".join(rows[row][column] for row in range(GRID_SIZE)) for column in range(GRID_SIZE)
    )
    dictionary = Dictionary(words, min_len=6, max_len=6)

    assert is_word_square(_solution_grid(rows), dictionary, GRID_SIZE)


def test_square_is_a_valid_double_word_square() -> None:
    d = _dict()
    square = build_square(d, seed=123)
    assert len(square) == GRID_SIZE
    assert all(len(row) == GRID_SIZE for row in square)
    assert is_word_square(_solution_grid(square), d, GRID_SIZE)


def test_square_uses_curated_vocabulary_and_is_not_symmetric() -> None:
    d = _dict()
    square = build_square(d, seed=123)
    columns = [
        "".join(square[row][column] for row in range(GRID_SIZE)) for column in range(GRID_SIZE)
    ]

    assert set(square).isdisjoint(columns)
    assert all(word in d or word[::-1] in d for word in square + columns)
    assert "SPEERS" not in d
    assert "SIRRAH" not in d


def test_selection_prefers_novel_vocabulary(monkeypatch: Any) -> None:
    repeated = ["ABCDEF", "GHIJKL", "MNOPQR", "STUVWX", "YZABCD", "EFGHIJ"]
    novel = ["KLMNOP", "QRSTUV", "WXYZAB", "CDEFGH", "IJKLMN", "OPQRST"]
    words = set(repeated + novel)
    for square in (repeated, novel):
        words.update("".join(square[row][column] for row in range(6)) for column in range(6))
    monkeypatch.setattr(word_square, "zipf_frequency", lambda word, language: 1.0)
    selected = _select_square(
        [repeated, novel],
        seed=0,
        recent_squares=[repeated],
    )
    selected_words = set(selected)
    selected_words.update(
        "".join(selected[row][column] for row in range(6)) for column in range(6)
    )
    novel_words = set(novel)
    novel_words.update("".join(novel[row][column] for row in range(6)) for column in range(6))
    assert selected_words == novel_words


def test_selection_prefers_familiar_vocabulary(monkeypatch: Any) -> None:
    unfamiliar = ["ABCDEF", "GHIJKL", "MNOPQR", "STUVWX", "YZABCD", "EFGHIJ"]
    familiar = ["KLMNOP", "QRSTUV", "WXYZAB", "CDEFGH", "IJKLMN", "OPQRST"]
    familiar_words = word_square._word_set(familiar)

    def frequency(word: str, language: str) -> float:
        assert language == "en"
        return 5.0 if word in familiar_words else 1.0

    monkeypatch.setattr(word_square, "zipf_frequency", frequency)

    assert _select_square([unfamiliar, familiar], seed=0, recent_squares=[]) == familiar


def test_familiarity_checks_both_reading_directions(monkeypatch: Any) -> None:
    def frequency(word: str, language: str) -> float:
        assert language == "en"
        return 5.0 if word == "BURNS" else 1.0

    monkeypatch.setattr(word_square, "zipf_frequency", frequency)

    assert word_square._word_familiarity("SNRUB") == 5.0


def test_search_avoids_recent_vocabulary(monkeypatch: Any) -> None:
    recent = ["BATTLE", "ADORED", "COKING", "UNEASE", "LINGER", "ASSESS"]
    recent_words = set(recent)
    recent_words.update("".join(recent[row][column] for row in range(6)) for column in range(6))
    avoided_words: set[str] = set()

    def solve(pool: list[str], **kwargs: object) -> tuple[list[list[str]], list[list[str]]]:
        avoided_words.update(kwargs["avoided_words"])  # type: ignore[arg-type]
        return [["GROOMS", "NEURON", "OPTIMA", "MEAGER", "ENGINE", "STENTS"]], []

    monkeypatch.setattr(word_square, "_solve_pool", solve)
    word_square.build_square(_dict(), seed=1, recent_squares=[recent])

    assert avoided_words == recent_words


def test_search_uses_repeated_fill_as_fallback(monkeypatch: Any) -> None:
    recent = ["BATTLE", "ADORED", "COKING", "UNEASE", "LINGER", "ASSESS"]
    fallback = ["GROOMS", "NEURON", "OPTIMA", "MEAGER", "ENGINE", "STENTS"]

    def solve(pool: list[str], **kwargs: object) -> tuple[list[list[str]], list[list[str]]]:
        return [], [fallback]

    monkeypatch.setattr(word_square, "_solve_pool", solve)
    selected = word_square.build_square(_dict(), seed=1, recent_squares=[recent])

    assert set(selected) | set(word_square._columns(selected)) == set(fallback) | set(
        word_square._columns(fallback)
    )


def test_search_spends_more_attempts_looking_for_novel_fill(monkeypatch: Any) -> None:
    recent = ["BATTLE", "ADORED", "COKING", "UNEASE", "LINGER", "ASSESS"]
    repeated = list(recent)
    novel = ["GROOMS", "NEURON", "OPTIMA", "MEAGER", "ENGINE", "STENTS"]
    calls = 0

    def solve(pool: list[str], **kwargs: object) -> tuple[list[list[str]], list[list[str]]]:
        nonlocal calls
        calls += 1
        if calls == 3:
            return [novel], []
        return [], [repeated]

    monkeypatch.setattr(word_square, "_MAX_ATTEMPTS", 2)
    monkeypatch.setattr(word_square, "_MAX_ATTEMPTS_WITH_HISTORY", 3)
    monkeypatch.setattr(word_square, "_solve_pool", solve)

    selected = build_square(_dict(), seed=1, recent_squares=[recent])
    assert set(selected) | set(word_square._columns(selected)) == set(novel) | set(
        word_square._columns(novel)
    )
    assert calls == 3


def test_search_rejects_heavily_repeated_fallback(monkeypatch: Any) -> None:
    recent = ["BATTLE", "ADORED", "COKING", "UNEASE", "LINGER", "ASSESS"]

    def solve(pool: list[str], **kwargs: object) -> tuple[list[list[str]], list[list[str]]]:
        return [], [recent]

    monkeypatch.setattr(word_square, "_MAX_ATTEMPTS_WITH_HISTORY", 1)
    monkeypatch.setattr(word_square, "_solve_pool", solve)

    with pytest.raises(word_square.WordSquareError, match="no sufficiently novel"):
        build_square(_dict(), seed=1, recent_squares=[recent])


def test_recent_solutions_loads_only_prior_valid_boards(tmp_path: Path) -> None:
    store = LocalStore(tmp_path)
    solution = ["ABCDEF"] * GRID_SIZE
    store.put("2026-01-01", json.dumps({"solution": solution}))
    store.put("2026-01-02", "not json")
    store.put("2026-01-04", json.dumps({"solution": solution}))

    assert _recent_solutions(store, "2026-01-03") == [solution]


def test_square_is_deterministic() -> None:
    d = get_dictionary(min_len=GRID_SIZE - 1, max_len=GRID_SIZE)
    a = build_square(d, seed=4242)
    b = build_square(d, seed=4242)
    assert a == b


def test_generated_board_matches_solution() -> None:
    board = generate_board(seed=777)
    assert board.size == GRID_SIZE
    assert len(board.solution) == GRID_SIZE
    d = get_dictionary(min_len=GRID_SIZE - 1, max_len=GRID_SIZE)
    # The completed board (fixed + blanks filled from solution) is a valid square.
    grid: list[list[str | None]] = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            grid[r][c] = board.solution[r][c]
    assert is_word_square(grid, d, GRID_SIZE - 1)
    assert len(board.blocked) == 2
    lines = [row.replace("#", "") for row in board.solution]
    lines.extend(word_square._columns(board.solution))
    assert sum(len(word) == GRID_SIZE - 1 for word in lines) == 4


def test_fixed_cells_are_subset_of_solution() -> None:
    board = generate_board(seed=999)
    for (r, c), ch in board.fixed.items():
        assert board.solution[r][c] == ch


def test_board_blanks_a_fraction_of_cells() -> None:
    board = generate_board(seed=555, outer_keep_ratio=0.5, inner_blank_ratio=2 / 3)
    total = board.size * board.size
    n_fixed = len(board.fixed)
    n_blank = total - n_fixed
    assert 0 < n_blank < total
    # At least one given in every row and column.
    for r in range(board.size):
        assert any((r, c) in board.fixed for c in range(board.size))
    for c in range(board.size):
        assert any((r, c) in board.fixed for r in range(board.size))


def test_blanking_keeps_most_outer_ring_and_blanks_most_of_middle() -> None:
    board = generate_board(seed=555)
    size = board.size
    outer = {
        (r, c)
        for r in range(size)
        for c in range(size)
        if r in (0, size - 1) or c in (0, size - 1)
    }
    outer_playable = outer - board.blocked
    inner = {
        (r, c)
        for r in range(size)
        for c in range(size)
        if r not in (0, size - 1) and c not in (0, size - 1)
    }
    n_outer_given = len(outer_playable & set(board.fixed))
    n_inner_blank = len(inner - set(board.fixed))
    assert 0.5 <= n_outer_given / len(outer_playable) <= 0.7
    assert 0.4 <= n_inner_blank / len(inner) <= 0.6


def test_generated_board_is_deterministic() -> None:
    a = generate_board(seed=2468)
    b = generate_board(seed=2468)
    assert a.solution == b.solution
    assert a.fixed == b.fixed


def test_board_supports_five_letter_lines_with_outer_block() -> None:
    rows = ["#ABCDE", "FGHIJK", "LMNOPQ", "RSTUVW", "XYZABC", "DEFGHI"]
    board = board_from_solution(rows, date="2026-09-13", seed=1)

    assert board.min_word_length == 5
    assert board.blocked == {(0, 0)}
    assert (0, 0) not in board.fixed


def test_board_rejects_interior_blocks() -> None:
    rows = ["ABCDEF", "G#IJKL", "MNOPQR", "STUVWX", "YZABCD", "EFGHIJ"]
    with pytest.raises(ValueError, match="outer ring"):
        board_from_solution(rows, date="2026-09-13")
