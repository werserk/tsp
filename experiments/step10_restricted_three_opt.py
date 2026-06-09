#!/usr/bin/env python3
"""Step 10: restricted 3-opt-like local search on the LKH tour."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.heuristics.restricted_three_opt import (
    improve_tour_restricted_three_opt,
    save_restricted_three_opt_result,
    select_long_edge_cut_positions,
)
from src.io.matrix_loader import load_matrix
from src.io.validation import validate_tour
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

SOURCE_ARTIFACT = Path("results/best/step6-lkh-best.json")
LOWER_BOUND_ARTIFACT = Path("results/best/step9-held-karp-one-tree.json")
OUTPUT_PATH = Path("results/runs/step10-restricted-three-opt.json")
COMMAND = "python experiments/step10_restricted_three_opt.py"
CUT_LIMIT = 32
MAX_PASSES = 2


def main() -> None:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    source_payload = json.loads((ROOT / SOURCE_ARTIFACT).read_text(encoding="utf-8"))
    lower_payload = json.loads((ROOT / LOWER_BOUND_ARTIFACT).read_text(encoding="utf-8"))
    source_tour = [int(city) for city in source_payload["tour"]]
    source_length = int(source_payload["length"])
    validate_tour(source_tour, data.n)
    checked_source_length = tour_length(data.matrix, source_tour, validate=False)
    if checked_source_length != source_length:
        raise AssertionError(f"source length mismatch: {checked_source_length} != {source_length}")

    cut_positions = select_long_edge_cut_positions(source_tour, data.matrix, limit=CUT_LIMIT)
    result = improve_tour_restricted_three_opt(
        data.matrix,
        source_tour,
        cut_positions=cut_positions,
        max_passes=MAX_PASSES,
    )
    validate_tour(result.tour, data.n)
    checked_length = tour_length(data.matrix, result.tour, validate=False)
    if checked_length != result.length:
        raise AssertionError(f"result length mismatch: {checked_length} != {result.length}")

    save_restricted_three_opt_result(
        result,
        output_path=ROOT / OUTPUT_PATH,
        input_file=CHALLENGE_MATRIX_PATH,
        source_artifact=SOURCE_ARTIFACT,
        n=data.n,
        command=COMMAND,
        lower_bound=float(lower_payload["lower_bound"]),
    )

    print(f"algorithm={result.algorithm}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"source_artifact={SOURCE_ARTIFACT}")
    print(f"n={data.n}")
    print(f"cut_limit={CUT_LIMIT}")
    print(f"max_passes={MAX_PASSES}")
    print(f"initial_length={result.initial_length}")
    print(f"length={result.length}")
    print(f"improvement={result.initial_length - result.length}")
    print(f"moves_applied={result.moves_applied}")
    print(f"candidate_cut_count={result.candidate_cut_count}")
    print(f"candidates_evaluated={result.candidates_evaluated}")
    print(f"lower_bound={float(lower_payload['lower_bound']):.6f}")
    print(f"absolute_gap={result.length - float(lower_payload['lower_bound']):.6f}")
    print(f"relative_gap={(result.length - float(lower_payload['lower_bound'])) / result.length:.6f}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
