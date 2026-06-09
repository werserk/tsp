#!/usr/bin/env python3
"""Step 2 smoke checks for TSP core infrastructure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io.matrix_loader import load_matrix
from src.io.validation import validate_tour
from src.tsp.tour import tour_length


def check_matrix(relative_path: str, expected_n: int) -> dict:
    path = ROOT / relative_path
    data = load_matrix(path)
    if data.n != expected_n:
        raise AssertionError(f"{relative_path}: expected n={expected_n}, got {data.n}")

    sequential_tour = list(range(data.n))
    validate_tour(sequential_tour, data.n)
    length = tour_length(data.matrix, sequential_tour)
    if length <= 0:
        raise AssertionError(f"{relative_path}: sequential tour length must be positive")

    return {
        "file": relative_path,
        "format": data.format,
        "n": data.n,
        "sequential_tour_length": length,
    }


def main() -> None:
    results = [
        check_matrix("data/raw/matrices/M.txt", 1114),
        check_matrix("data/raw/matrices/tsp_matrix1.txt", 94),
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
