from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from src.heuristics.nearest_neighbor import nearest_neighbor_tour
from src.heuristics.two_opt import TWO_OPT_STRATEGY, improve_tour_two_opt
from src.io.validation import validate_matrix, validate_tour
from src.tsp.tour import tour_length
from src.tsp.types import City, Matrix, Tour

MULTISTART_NN_TWO_OPT_ALGORITHM = "multistart_nearest_neighbor_two_opt"
MULTISTART_NN_TWO_OPT_STRATEGY = "nearest_neighbor_then_two_opt"


@dataclass(frozen=True)
class StartCandidate:
    start_city: City
    length: int
    tour: Tour


@dataclass(frozen=True)
class MultiStartTwoOptResult:
    algorithm: str
    length: int
    tour: Tour
    best_start_city: City
    best_initial_length: int
    starts_checked: int
    total_two_opt_moves: int
    metadata: dict[str, Any]


def rank_starts_by_nearest_neighbor_length(
    matrix: Matrix,
    starts: Iterable[City],
    *,
    limit: int | None = None,
) -> list[StartCandidate]:
    """Rank start cities by their nearest-neighbor tour length."""

    validate_matrix(matrix)
    n = len(matrix)
    candidates: list[StartCandidate] = []
    for start_city in starts:
        tour = nearest_neighbor_tour(matrix, start_city)
        validate_tour(tour, n)
        candidates.append(
            StartCandidate(
                start_city=start_city,
                length=tour_length(matrix, tour, validate=False),
                tour=tour,
            )
        )
    candidates.sort(key=lambda item: (item.length, item.start_city))
    if limit is None:
        return candidates
    return candidates[:limit]


def multistart_nearest_neighbor_two_opt(matrix: Matrix, starts: Iterable[City]) -> MultiStartTwoOptResult:
    """Run nearest-neighbor + 2-opt for multiple starts and return the best tour."""

    validate_matrix(matrix)
    n = len(matrix)
    starts_checked = 0
    total_two_opt_moves = 0
    best_result: MultiStartTwoOptResult | None = None

    for start_city in starts:
        initial_tour = nearest_neighbor_tour(matrix, start_city)
        validate_tour(initial_tour, n)
        initial_length = tour_length(matrix, initial_tour, validate=False)
        improved = improve_tour_two_opt(matrix, initial_tour)
        validate_tour(improved.tour, n)
        independently_checked_length = tour_length(matrix, improved.tour, validate=False)
        if independently_checked_length != improved.length:
            raise AssertionError(
                "independent tour length check mismatch: "
                f"{independently_checked_length} != {improved.length}"
            )

        starts_checked += 1
        total_two_opt_moves += improved.moves_applied
        candidate = MultiStartTwoOptResult(
            algorithm=MULTISTART_NN_TWO_OPT_ALGORITHM,
            length=improved.length,
            tour=improved.tour,
            best_start_city=start_city,
            best_initial_length=initial_length,
            starts_checked=starts_checked,
            total_two_opt_moves=total_two_opt_moves,
            metadata={
                "strategy": MULTISTART_NN_TWO_OPT_STRATEGY,
                "two_opt_strategy": TWO_OPT_STRATEGY,
                "best_initial_length": initial_length,
            },
        )
        if best_result is None or candidate.length < best_result.length:
            best_result = candidate

    if best_result is None:
        raise ValueError("at least one start city is required")

    return MultiStartTwoOptResult(
        algorithm=best_result.algorithm,
        length=best_result.length,
        tour=best_result.tour,
        best_start_city=best_result.best_start_city,
        best_initial_length=best_result.best_initial_length,
        starts_checked=starts_checked,
        total_two_opt_moves=total_two_opt_moves,
        metadata={
            "strategy": MULTISTART_NN_TWO_OPT_STRATEGY,
            "two_opt_strategy": TWO_OPT_STRATEGY,
            "best_initial_length": best_result.best_initial_length,
        },
    )


def multistart_two_opt_payload(
    result: MultiStartTwoOptResult,
    *,
    input_file: Path,
    n: int,
    command: str,
    current_best_upper_bound: int | None = None,
    lower_bound: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "n": n,
        "length": result.length,
        "best_start_city": result.best_start_city,
        "best_initial_length": result.best_initial_length,
        "starts_checked": result.starts_checked,
        "total_two_opt_moves": result.total_two_opt_moves,
        "tour": result.tour,
        "metadata": result.metadata,
        "command": command,
        "created_at": datetime.now(UTC).isoformat(),
    }
    if current_best_upper_bound is not None:
        payload["previous_upper_bound"] = current_best_upper_bound
        payload["improvement_over_previous_upper_bound"] = current_best_upper_bound - result.length
    if lower_bound is not None:
        payload["lower_bound"] = lower_bound
        payload["absolute_gap"] = result.length - lower_bound
        payload["relative_gap"] = (result.length - lower_bound) / result.length
    return payload


def save_multistart_two_opt_result(
    result: MultiStartTwoOptResult,
    *,
    output_path: Path,
    input_file: Path,
    n: int,
    command: str,
    current_best_upper_bound: int | None = None,
    lower_bound: int | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = multistart_two_opt_payload(
        result,
        input_file=input_file,
        n=n,
        command=command,
        current_best_upper_bound=current_best_upper_bound,
        lower_bound=lower_bound,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
