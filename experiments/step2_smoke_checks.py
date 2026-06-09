#!/usr/bin/env python3
"""Step 2 smoke checks for TSP core infrastructure."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io.matrix_loader import load_matrix
from src.io.validation import validate_tour
from src.tsp.constants import (
    CHALLENGE_CITY_COUNT,
    CHALLENGE_MATRIX_PATH,
    LECTURE_SAMPLE_CITY_COUNT,
    LECTURE_SAMPLE_MATRIX_PATH,
)
from src.tsp.tour import tour_length


@dataclass(frozen=True)
class MatrixSmokeCase:
    relative_path: Path
    expected_n: int


SMOKE_CASES = (
    MatrixSmokeCase(CHALLENGE_MATRIX_PATH, CHALLENGE_CITY_COUNT),
    MatrixSmokeCase(LECTURE_SAMPLE_MATRIX_PATH, LECTURE_SAMPLE_CITY_COUNT),
)


def run_smoke_case(case: MatrixSmokeCase, *, root: Path = ROOT) -> dict[str, Any]:
    path = root / case.relative_path
    data = load_matrix(path)
    if data.n != case.expected_n:
        raise AssertionError(f"{case.relative_path}: expected n={case.expected_n}, got {data.n}")

    sequential_tour = list(range(data.n))
    validate_tour(sequential_tour, data.n)
    length = tour_length(data.matrix, sequential_tour, validate=False)
    if length <= 0:
        raise AssertionError(f"{case.relative_path}: sequential tour length must be positive")

    return {
        "file": str(case.relative_path),
        "format": data.format,
        "n": data.n,
        "sequential_tour_length": length,
    }


def main() -> None:
    results = [run_smoke_case(case) for case in SMOKE_CASES]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
