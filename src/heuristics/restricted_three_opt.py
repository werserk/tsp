from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from src.io.validation import validate_matrix, validate_tour
from src.tsp.tour import tour_length
from src.tsp.types import Matrix, Tour

RESTRICTED_THREE_OPT_ALGORITHM = "restricted_three_opt_local_search"
RESTRICTED_THREE_OPT_STRATEGY = "bounded_candidate_cut_reconnection"


@dataclass(frozen=True)
class RestrictedThreeOptResult:
    algorithm: str
    initial_length: int
    length: int
    tour: Tour
    moves_applied: int
    passes: int
    candidate_cut_count: int
    candidates_evaluated: int
    metadata: dict[str, Any]


def improve_tour_restricted_three_opt(
    matrix: Matrix,
    initial_tour: Tour,
    *,
    cut_positions: Iterable[int],
    max_passes: int = 1,
) -> RestrictedThreeOptResult:
    """Improve a tour by testing bounded 3-cut segment reconnections."""

    validate_matrix(matrix)
    validate_tour(initial_tour, len(matrix))
    if max_passes <= 0:
        raise ValueError("max_passes must be positive")

    tour = list(initial_tour)
    current_length = tour_length(matrix, tour, validate=False)
    initial_length = current_length
    cuts = _normalized_cut_positions(cut_positions, len(tour))
    moves_applied = 0
    candidates_evaluated = 0
    passes = 0

    for _pass_index in range(max_passes):
        passes += 1
        move = _find_first_improving_reconnection(matrix, tour, cuts, current_length)
        if move is None:
            break
        tour, current_length, evaluated = move
        candidates_evaluated += evaluated
        moves_applied += 1
    else:
        passes = max_passes

    if moves_applied == 0:
        # Count the exhausted search once for transparent artifact metadata.
        candidates_evaluated = _count_candidate_reconnections(cuts)

    return RestrictedThreeOptResult(
        algorithm=RESTRICTED_THREE_OPT_ALGORITHM,
        initial_length=initial_length,
        length=current_length,
        tour=tour,
        moves_applied=moves_applied,
        passes=passes,
        candidate_cut_count=len(cuts),
        candidates_evaluated=candidates_evaluated,
        metadata={"strategy": RESTRICTED_THREE_OPT_STRATEGY},
    )


def select_long_edge_cut_positions(tour: Tour, matrix: Matrix, *, limit: int) -> list[int]:
    """Return cut positions after the longest tour edges, excluding position 0."""

    validate_matrix(matrix)
    validate_tour(tour, len(matrix))
    if limit <= 0:
        raise ValueError("limit must be positive")

    n = len(tour)
    ranked_positions = []
    for position in range(1, n):
        from_city = tour[position - 1]
        to_city = tour[position]
        ranked_positions.append((matrix[from_city][to_city], position))
    ranked_positions.sort(key=lambda item: (-item[0], item[1]))
    return sorted(position for _weight, position in ranked_positions[:limit])


def restricted_three_opt_payload(
    result: RestrictedThreeOptResult,
    *,
    input_file: Path,
    source_artifact: Path,
    n: int,
    command: str,
    lower_bound: int | float | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "source_artifact": str(source_artifact),
        "n": n,
        "initial_length": result.initial_length,
        "length": result.length,
        "improvement": result.initial_length - result.length,
        "moves_applied": result.moves_applied,
        "passes": result.passes,
        "candidate_cut_count": result.candidate_cut_count,
        "candidates_evaluated": result.candidates_evaluated,
        "tour": result.tour,
        "metadata": result.metadata,
        "command": command,
        "created_at": datetime.now(UTC).isoformat(),
    }
    if lower_bound is not None:
        payload["lower_bound"] = lower_bound
        payload["absolute_gap"] = result.length - lower_bound
        payload["relative_gap"] = (result.length - lower_bound) / result.length
    return payload


def save_restricted_three_opt_result(
    result: RestrictedThreeOptResult,
    *,
    output_path: Path,
    input_file: Path,
    source_artifact: Path,
    n: int,
    command: str,
    lower_bound: int | float | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = restricted_three_opt_payload(
        result,
        input_file=input_file,
        source_artifact=source_artifact,
        n=n,
        command=command,
        lower_bound=lower_bound,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_first_improving_reconnection(
    matrix: Matrix,
    tour: Tour,
    cuts: list[int],
    current_length: int,
) -> tuple[Tour, int, int] | None:
    evaluated = 0
    for i, j, k in combinations(cuts, 3):
        for candidate in _three_cut_reconnections(tour, i, j, k):
            evaluated += 1
            candidate_length = tour_length(matrix, candidate, validate=False)
            if candidate_length < current_length:
                return candidate, candidate_length, evaluated
    return None


def _three_cut_reconnections(tour: Tour, i: int, j: int, k: int) -> list[Tour]:
    prefix = tour[:i]
    first = tour[i:j]
    second = tour[j:k]
    suffix = tour[k:]
    return [
        prefix + second + first + suffix,
        prefix + list(reversed(second)) + first + suffix,
        prefix + second + list(reversed(first)) + suffix,
        prefix + list(reversed(second)) + list(reversed(first)) + suffix,
        prefix + list(reversed(first)) + second + suffix,
        prefix + first + list(reversed(second)) + suffix,
        prefix + list(reversed(first)) + list(reversed(second)) + suffix,
    ]


def _normalized_cut_positions(cut_positions: Iterable[int], n: int) -> list[int]:
    cuts = sorted(set(cut_positions))
    if len(cuts) < 3:
        raise ValueError("at least three cut positions are required")
    if any(position <= 0 or position >= n for position in cuts):
        raise ValueError(f"cut positions must be in 1..{n - 1}")
    return cuts


def _count_candidate_reconnections(cuts: list[int]) -> int:
    return sum(7 for _ in combinations(cuts, 3))
