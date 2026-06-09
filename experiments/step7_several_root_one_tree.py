#!/usr/bin/env python3
"""Step 7: several-root 1-tree lower-bound baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bounds.one_tree import best_one_tree_lower_bound, save_several_root_one_tree_result
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH

UPPER_BOUND_ARTIFACT = Path("results/best/step6-lkh-best.json")
PROOF_NOTE = Path("notes/09-step7-several-root-one-tree.md")
OUTPUT_PATH = Path("results/best/step7-several-root-one-tree.json")
COMMAND = "python experiments/step7_several_root_one_tree.py"
CANDIDATE_ROOT_STRIDE = 16


def candidate_roots(n: int) -> list[int]:
    roots = list(range(0, n, CANDIDATE_ROOT_STRIDE))
    if roots[-1] != n - 1:
        roots.append(n - 1)
    return roots


def main() -> None:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    upper_bound_payload = json.loads((ROOT / UPPER_BOUND_ARTIFACT).read_text(encoding="utf-8"))
    upper_bound = int(upper_bound_payload["length"])

    roots = candidate_roots(data.n)
    result = best_one_tree_lower_bound(data.matrix, candidate_roots=roots)
    if result.lower_bound > upper_bound:
        raise AssertionError(
            "lower bound exceeds known upper bound; implementation/proof likely invalid: "
            f"{result.lower_bound} > {upper_bound}"
        )

    save_several_root_one_tree_result(
        result,
        output_path=ROOT / OUTPUT_PATH,
        input_file=CHALLENGE_MATRIX_PATH,
        n=data.n,
        upper_bound=upper_bound,
        upper_bound_artifact=UPPER_BOUND_ARTIFACT,
        proof_note=PROOF_NOTE,
        command=COMMAND,
    )

    print(f"algorithm={result.algorithm}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"candidate_count={len(result.candidate_roots)}")
    print(f"best_root_city={result.best_root_city}")
    print(f"lower_bound={result.lower_bound}")
    print(f"upper_bound={upper_bound}")
    print(f"absolute_gap={upper_bound - result.lower_bound}")
    print(f"relative_gap={(upper_bound - result.lower_bound) / upper_bound:.6f}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
