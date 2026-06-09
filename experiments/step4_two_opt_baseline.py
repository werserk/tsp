#!/usr/bin/env python3
"""Step 4: improve current best upper bound with 2-opt local search."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.heuristics.two_opt import improve_tour_two_opt, save_two_opt_result
from src.io.matrix_loader import load_matrix
from src.io.validation import validate_tour
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

SOURCE_ARTIFACT = Path("results/best/step3-nearest-neighbor-best.json")
OUTPUT_PATH = Path("results/best/step4-two-opt-best.json")
COMMAND = "python experiments/step4_two_opt_baseline.py"


def main() -> None:
    matrix_path = ROOT / CHALLENGE_MATRIX_PATH
    source_path = ROOT / SOURCE_ARTIFACT
    source = json.loads(source_path.read_text(encoding="utf-8"))

    data = load_matrix(matrix_path)
    initial_tour = source["tour"]
    validate_tour(initial_tour, data.n)

    source_length = int(source["length"])
    independently_checked_source_length = tour_length(data.matrix, initial_tour, validate=True)
    if independently_checked_source_length != source_length:
        raise AssertionError(
            "source artifact length mismatch: "
            f"{independently_checked_source_length} != {source_length}"
        )

    result = improve_tour_two_opt(data.matrix, initial_tour)
    independently_checked_length = tour_length(data.matrix, result.tour, validate=True)
    if independently_checked_length != result.length:
        raise AssertionError(
            "independent tour length check mismatch: "
            f"{independently_checked_length} != {result.length}"
        )

    save_two_opt_result(
        result,
        output_path=ROOT / OUTPUT_PATH,
        input_file=CHALLENGE_MATRIX_PATH,
        source_artifact=SOURCE_ARTIFACT,
        n=data.n,
        command=COMMAND,
    )

    print(f"algorithm={result.algorithm}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"source_artifact={SOURCE_ARTIFACT}")
    print(f"n={data.n}")
    print(f"initial_length={result.initial_length}")
    print(f"best_length={result.length}")
    print(f"improvement={result.initial_length - result.length}")
    print(f"moves_applied={result.moves_applied}")
    print(f"passes={result.passes}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
