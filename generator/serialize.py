"""Serialize a generated :class:`Board` into the JSON the frontend expects.

The hidden solution (the full square's across-words) powers Reveal; real
validation is open-ended against the dictionary, so the payload never encodes a
single "correct answer".
"""

from __future__ import annotations

from typing import Any

from generator.models import Board


def board_to_dict(board: Board) -> dict[str, Any]:
    grid: list[list[dict[str, Any] | None]] = []
    for r in range(board.size):
        row: list[dict[str, Any] | None] = []
        for c in range(board.size):
            letter = board.fixed.get((r, c))
            if (r, c) in board.blocked:
                row.append({"blocked": True})
            else:
                row.append({"fixed": letter} if letter is not None else None)
        grid.append(row)

    return {
        "date": board.date,
        "size": board.size,
        "minWordLength": board.min_word_length,
        "grid": grid,
        "solution": board.solution,
    }


def board_to_json(board: Board) -> str:
    import json

    return json.dumps(board_to_dict(board), ensure_ascii=False, indent=2)
