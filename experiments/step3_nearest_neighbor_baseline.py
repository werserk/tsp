#!/usr/bin/env python3
"""Step 3: multi-start nearest-neighbor upper-bound baseline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.heuristics.nearest_neighbor import multi_start_nearest_neighbor, save_tour_result
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

OUTPUT_PATH = Path("results/best/step3-nearest-neighbor-best.json")
COMMAND = "python experiments/step3_nearest_neighbor_baseline.py"


def main() -> None:
    matrix_path = ROOT / CHALLENGE_MATRIX_PATH
    data = load_matrix(matrix_path)
    result = multi_start_nearest_neighbor(data.matrix, starts=range(data.n))

    independently_checked_length = tour_length(data.matrix, result.tour, validate=True)
    if independently_checked_length != result.length:
        raise AssertionError(
            "independent tour length check mismatch: "
            f"{independently_checked_length} != {result.length}"
        )

    output_path = ROOT / OUTPUT_PATH
    save_tour_result(
        result,
        output_path=output_path,
        input_file=CHALLENGE_MATRIX_PATH,
        n=data.n,
        command=COMMAND,
    )

    print(f"algorithm={result.algorithm}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"starts_checked={result.metadata['starts_checked']}")
    print(f"best_start={result.start_city}")
    print(f"best_length={result.length}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
