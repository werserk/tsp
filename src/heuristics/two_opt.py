from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.io.validation import validate_matrix, validate_tour
from src.tsp.tour import tour_length
from src.tsp.types import Matrix, Tour

TWO_OPT_FIRST_IMPROVEMENT_ALGORITHM = "two_opt_first_improvement"
TWO_OPT_STRATEGY = "first_improvement"


@dataclass(frozen=True)
class TwoOptResult:
    algorithm: str
    initial_length: int
    length: int
    tour: Tour
    moves_applied: int
    passes: int
    metadata: dict[str, Any]


def improve_tour_two_opt(matrix: Matrix, initial_tour: Tour) -> TwoOptResult:
    """Improve a valid tour with deterministic 2-opt first improvement."""

    validate_matrix(matrix)
    validate_tour(initial_tour, len(matrix))

    tour = list(initial_tour)
    initial_length = tour_length(matrix, tour, validate=False)
    current_length = initial_length
    moves_applied = 0
    passes = 0

    while True:
        passes += 1
        move = _find_first_improving_move(matrix, tour)
        if move is None:
            break

        i, k, delta = move
        tour = apply_two_opt_move(tour, i=i, k=k)
        current_length += delta
        moves_applied += 1

    return TwoOptResult(
        algorithm=TWO_OPT_FIRST_IMPROVEMENT_ALGORITHM,
        initial_length=initial_length,
        length=current_length,
        tour=tour,
        moves_applied=moves_applied,
        passes=passes,
        metadata={"strategy": TWO_OPT_STRATEGY},
    )


def two_opt_delta(matrix: Matrix, tour: Tour, *, i: int, k: int) -> int:
    """Return length change if tour[i:k+1] is reversed."""

    n = len(tour)
    previous_city = tour[i - 1]
    first_reversed_city = tour[i]
    last_reversed_city = tour[k]
    next_city = tour[(k + 1) % n]

    removed = matrix[previous_city][first_reversed_city] + matrix[last_reversed_city][next_city]
    added = matrix[previous_city][last_reversed_city] + matrix[first_reversed_city][next_city]
    return added - removed


def apply_two_opt_move(tour: Tour, *, i: int, k: int) -> Tour:
    """Return a new tour after reversing the segment i..k inclusive."""

    return tour[:i] + list(reversed(tour[i : k + 1])) + tour[k + 1 :]


def two_opt_payload(
    result: TwoOptResult,
    *,
    input_file: Path,
    source_artifact: Path,
    n: int,
    command: str,
) -> dict[str, Any]:
    return {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "source_artifact": str(source_artifact),
        "n": n,
        "initial_length": result.initial_length,
        "length": result.length,
        "improvement": result.initial_length - result.length,
        "moves_applied": result.moves_applied,
        "passes": result.passes,
        "tour": result.tour,
        "metadata": result.metadata,
        "command": command,
        "created_at": datetime.now(UTC).isoformat(),
    }


def save_two_opt_result(
    result: TwoOptResult,
    *,
    output_path: Path,
    input_file: Path,
    source_artifact: Path,
    n: int,
    command: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = two_opt_payload(
        result,
        input_file=input_file,
        source_artifact=source_artifact,
        n=n,
        command=command,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_first_improving_move(matrix: Matrix, tour: Tour) -> tuple[int, int, int] | None:
    n = len(tour)
    for i in range(1, n - 1):
        for k in range(i + 1, n):
            if _would_reverse_entire_cycle(i, k, n):
                continue
            delta = two_opt_delta(matrix, tour, i=i, k=k)
            if delta < 0:
                return i, k, delta
    return None


def _would_reverse_entire_cycle(i: int, k: int, n: int) -> bool:
    return i == 0 and k == n - 1
