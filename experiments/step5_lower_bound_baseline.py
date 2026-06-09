#!/usr/bin/env python3
"""Step 5: MST and simple 1-tree lower-bound baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bounds.mst import minimum_spanning_tree
from src.bounds.one_tree import one_tree_lower_bound, save_one_tree_result
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH

ROOT_CITY = 0
UPPER_BOUND_ARTIFACT = Path("results/best/step4-two-opt-best.json")
PROOF_NOTE = Path("notes/06-step5-lower-bound-mst-one-tree.md")
OUTPUT_PATH = Path("results/best/step5-lower-bound-baseline.json")
COMMAND = "python experiments/step5_lower_bound_baseline.py"


def main() -> None:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    upper_bound_payload = json.loads((ROOT / UPPER_BOUND_ARTIFACT).read_text(encoding="utf-8"))
    upper_bound = int(upper_bound_payload["length"])

    mst_result = minimum_spanning_tree(data.matrix)
    one_tree_result = one_tree_lower_bound(data.matrix, root_city=ROOT_CITY)
    if one_tree_result.lower_bound < mst_result.weight:
        raise AssertionError(
            "1-tree lower bound should not be smaller than full MST baseline: "
            f"{one_tree_result.lower_bound} < {mst_result.weight}"
        )
    if one_tree_result.lower_bound > upper_bound:
        raise AssertionError(
            "lower bound exceeds known upper bound; implementation/proof likely invalid: "
            f"{one_tree_result.lower_bound} > {upper_bound}"
        )

    save_one_tree_result(
        one_tree_result,
        output_path=ROOT / OUTPUT_PATH,
        input_file=CHALLENGE_MATRIX_PATH,
        n=data.n,
        upper_bound=upper_bound,
        upper_bound_artifact=UPPER_BOUND_ARTIFACT,
        proof_note=PROOF_NOTE,
        command=COMMAND,
    )

    print(f"algorithm={one_tree_result.algorithm}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"root_city={one_tree_result.root_city}")
    print(f"mst_weight={mst_result.weight}")
    print(f"mst_without_root_weight={one_tree_result.mst_without_root_weight}")
    print(f"root_edges={one_tree_result.root_edges}")
    print(f"lower_bound={one_tree_result.lower_bound}")
    print(f"upper_bound={upper_bound}")
    print(f"absolute_gap={upper_bound - one_tree_result.lower_bound}")
    print(f"relative_gap={(upper_bound - one_tree_result.lower_bound) / upper_bound:.6f}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
