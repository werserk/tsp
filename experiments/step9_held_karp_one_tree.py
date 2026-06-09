#!/usr/bin/env python3
"""Step 9: Held-Karp-style Lagrangian 1-tree lower-bound baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bounds.held_karp import optimize_held_karp_one_tree, save_held_karp_one_tree_result
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH

UPPER_BOUND_ARTIFACT = Path("results/best/step6-lkh-best.json")
PREVIOUS_LOWER_BOUND_ARTIFACT = Path("results/best/step7-several-root-one-tree.json")
PROOF_NOTE = Path("notes/11-step9-held-karp-one-tree.md")
OUTPUT_PATH = Path("results/best/step9-held-karp-one-tree.json")
COMMAND = "python experiments/step9_held_karp_one_tree.py"

ROOT_CITY = 0
ITERATIONS = 120
INITIAL_STEP_SIZE = 64.0
STEP_DECAY = 0.96


def main() -> None:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    upper_bound_payload = json.loads((ROOT / UPPER_BOUND_ARTIFACT).read_text(encoding="utf-8"))
    upper_bound = int(upper_bound_payload["length"])

    previous_lower_bound_payload = json.loads(
        (ROOT / PREVIOUS_LOWER_BOUND_ARTIFACT).read_text(encoding="utf-8")
    )
    previous_lower_bound = float(previous_lower_bound_payload["lower_bound"])

    parameters = {
        "root_city": ROOT_CITY,
        "iterations": ITERATIONS,
        "initial_step_size": INITIAL_STEP_SIZE,
        "step_decay": STEP_DECAY,
    }
    result = optimize_held_karp_one_tree(
        data.matrix,
        root_city=ROOT_CITY,
        iterations=ITERATIONS,
        initial_step_size=INITIAL_STEP_SIZE,
        step_decay=STEP_DECAY,
    )
    if result.best_lower_bound > upper_bound:
        raise AssertionError(
            "lower bound exceeds known upper bound; implementation/proof likely invalid: "
            f"{result.best_lower_bound} > {upper_bound}"
        )

    save_held_karp_one_tree_result(
        result,
        output_path=ROOT / OUTPUT_PATH,
        input_file=CHALLENGE_MATRIX_PATH,
        n=data.n,
        upper_bound=upper_bound,
        upper_bound_artifact=UPPER_BOUND_ARTIFACT,
        previous_lower_bound_artifact=PREVIOUS_LOWER_BOUND_ARTIFACT,
        proof_note=PROOF_NOTE,
        command=COMMAND,
        parameters=parameters,
    )

    print(f"algorithm={result.algorithm}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"root_city={ROOT_CITY}")
    print(f"iterations_requested={ITERATIONS}")
    print(f"iterations_run={result.iteration_count}")
    print(f"best_iteration={result.best_iteration}")
    print(f"lower_bound={result.best_lower_bound:.6f}")
    print(f"previous_lower_bound={previous_lower_bound:.6f}")
    print(f"improvement_vs_previous={result.best_lower_bound - previous_lower_bound:.6f}")
    print(f"upper_bound={upper_bound}")
    print(f"absolute_gap={upper_bound - result.best_lower_bound:.6f}")
    print(f"relative_gap={(upper_bound - result.best_lower_bound) / upper_bound:.6f}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
