from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from src.io.validation import validate_matrix, validate_tour
from src.tsp.tour import tour_length
from src.tsp.types import City, Matrix, Tour

NEAREST_NEIGHBOR_ALGORITHM = "nearest_neighbor"
NEAREST_NEIGHBOR_MULTI_START_ALGORITHM = "nearest_neighbor_multi_start"


@dataclass(frozen=True)
class TourResult:
    algorithm: str
    tour: Tour
    length: int
    start_city: City
    metadata: dict[str, Any]


def nearest_neighbor_tour(matrix: Matrix, start_city: City) -> Tour:
    """Build a nearest-neighbor tour from one start city.

    Ties are broken by the lowest city index to keep runs deterministic.
    """

    n = len(matrix)
    _validate_start_city(start_city, n)

    visited = [False] * n
    tour = [start_city]
    visited[start_city] = True
    current_city = start_city

    while len(tour) < n:
        next_city = _nearest_unvisited_city(matrix[current_city], visited)
        tour.append(next_city)
        visited[next_city] = True
        current_city = next_city

    return tour


def multi_start_nearest_neighbor(matrix: Matrix, starts: Iterable[City]) -> TourResult:
    """Run nearest-neighbor from multiple starts and return the best valid tour."""

    validate_matrix(matrix)
    starts_checked = 0
    best: TourResult | None = None

    for start_city in starts:
        tour = nearest_neighbor_tour(matrix, start_city)
        validate_tour(tour, len(matrix))
        length = tour_length(matrix, tour, validate=False)
        starts_checked += 1

        if best is None or length < best.length:
            best = TourResult(
                algorithm=NEAREST_NEIGHBOR_MULTI_START_ALGORITHM,
                tour=tour,
                length=length,
                start_city=start_city,
                metadata={"starts_checked": starts_checked},
            )

    if best is None:
        raise ValueError("at least one start city is required")

    return TourResult(
        algorithm=best.algorithm,
        tour=best.tour,
        length=best.length,
        start_city=best.start_city,
        metadata={"starts_checked": starts_checked},
    )


def result_to_json_payload(
    result: TourResult,
    *,
    input_file: Path,
    n: int,
    command: str,
) -> dict[str, Any]:
    """Create a stable JSON-serializable upper-bound artifact."""

    return {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "n": n,
        "length": result.length,
        "start_city": result.start_city,
        "tour": result.tour,
        "metadata": result.metadata,
        "command": command,
        "created_at": datetime.now(UTC).isoformat(),
    }


def save_tour_result(
    result: TourResult,
    *,
    output_path: Path,
    input_file: Path,
    n: int,
    command: str,
) -> None:
    """Persist a tour result as formatted JSON."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = result_to_json_payload(result, input_file=input_file, n=n, command=command)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _validate_start_city(start_city: City, n: int) -> None:
    if start_city < 0 or start_city >= n:
        raise ValueError(f"start city out of range: {start_city}, expected 0..{n - 1}")


def _nearest_unvisited_city(distances: list[int], visited: list[bool]) -> City:
    best_city: City | None = None
    best_distance: int | None = None

    for city, distance in enumerate(distances):
        if visited[city]:
            continue
        if best_distance is None or distance < best_distance:
            best_city = city
            best_distance = distance

    if best_city is None:
        raise ValueError("no unvisited city remains")
    return best_city
