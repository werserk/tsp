#!/usr/bin/env python3
"""Step 13: stronger Held-Karp-style Lagrangian 1-tree lower bound."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bounds.held_karp import adjusted_one_tree_lower_bound, optimize_held_karp_one_tree
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH

UPPER_BOUND_ARTIFACT = Path("results/best/step6-lkh-best.json")
PREVIOUS_LOWER_BOUND_ARTIFACT = Path("results/best/step9-held-karp-one-tree.json")
PROOF_NOTE = Path("notes/15-step13-held-karp-decay-099-lower-bound.md")
OUTPUT_PATH = Path("results/best/step13-held-karp-decay-099-lower-bound.json")
COMMAND = "python experiments/step13_held_karp_decay_099.py"

ROOT_CITY = 0
ITERATIONS = 1000
INITIAL_STEP_SIZE = 64.0
STEP_DECAY = 0.99


def build_payload() -> dict[str, object]:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    upper_payload = json.loads((ROOT / UPPER_BOUND_ARTIFACT).read_text(encoding="utf-8"))
    previous_payload = json.loads((ROOT / PREVIOUS_LOWER_BOUND_ARTIFACT).read_text(encoding="utf-8"))
    upper_bound = int(upper_payload["length"])
    previous_lower_bound = float(previous_payload["lower_bound"])

    parameters = {
        "root_city": ROOT_CITY,
        "iterations": ITERATIONS,
        "initial_step_size": INITIAL_STEP_SIZE,
        "step_decay": STEP_DECAY,
        "selection": "continue Step 9 fixed-step subgradient ascent with slower decay; keep max over all penalty vectors",
    }

    started = perf_counter()
    result = optimize_held_karp_one_tree(
        data.matrix,
        root_city=ROOT_CITY,
        iterations=ITERATIONS,
        initial_step_size=INITIAL_STEP_SIZE,
        step_decay=STEP_DECAY,
    )
    runtime_seconds = perf_counter() - started
    independent = adjusted_one_tree_lower_bound(
        data.matrix,
        root_city=ROOT_CITY,
        penalties=result.best_penalties,
    )
    if abs(independent.lower_bound - result.best_lower_bound) > 1e-7:
        raise AssertionError(
            f"independent penalty recomputation mismatch: {independent.lower_bound} != {result.best_lower_bound}"
        )
    if result.best_lower_bound <= previous_lower_bound:
        raise AssertionError(f"not a strict improvement: {result.best_lower_bound} <= {previous_lower_bound}")
    if result.best_lower_bound > upper_bound:
        raise AssertionError(f"lower bound exceeds known upper bound: {result.best_lower_bound} > {upper_bound}")

    absolute_gap = upper_bound - result.best_lower_bound
    degree_deviations = [degree - 2 for degree in independent.degrees]
    return {
        "type": "lower_bound",
        "algorithm": result.algorithm,
        "method": "held_karp_lagrangian_one_tree_fixed_step_slow_decay",
        "input_matrix": str(CHALLENGE_MATRIX_PATH),
        "n": data.n,
        "root_city": result.root_city,
        "lower_bound": result.best_lower_bound,
        "previous_lower_bound": previous_lower_bound,
        "previous_lower_bound_artifact": str(PREVIOUS_LOWER_BOUND_ARTIFACT),
        "upper_bound": upper_bound,
        "upper_bound_artifact": str(UPPER_BOUND_ARTIFACT),
        "absolute_gap": absolute_gap,
        "relative_gap_to_lower": absolute_gap / result.best_lower_bound,
        "relative_gap_to_upper": absolute_gap / upper_bound,
        "integer_lower_bound": int(result.best_lower_bound) + 1,
        "best_iteration": result.best_iteration,
        "iteration_count": result.iteration_count,
        "parameters": parameters,
        "runtime_seconds": runtime_seconds,
        "best_penalties": result.best_penalties,
        "best_one_tree_degree_violation_l1": sum(abs(value) for value in degree_deviations),
        "best_one_tree_degree_violation_linf": max(abs(value) for value in degree_deviations),
        "precision_policy": "float64 arithmetic; bound is reported as computed, integer-friendly lower bound uses ceil because all input distances are integers",
        "proof_sketch": "For any node penalties pi, every Hamiltonian cycle has adjusted cost c(H)+2*sum(pi). The minimum adjusted 1-tree has adjusted cost no larger than any Hamiltonian cycle, so adjusted_1_tree_weight-2*sum(pi) <= OPT. Taking the best value over iterations preserves validity.",
        "verification": {
            "independent_recompute": "adjusted_one_tree_lower_bound(matrix, root_city, saved best_penalties)",
            "recomputed_lower_bound": independent.lower_bound,
            "matches_optimizer_best": True,
            "lower_bound_le_upper_bound": result.best_lower_bound <= upper_bound,
            "strict_improvement": result.best_lower_bound > previous_lower_bound,
        },
        "proof_note": str(PROOF_NOTE),
        "command": COMMAND,
        "created_at": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    payload = build_payload()
    output = ROOT / OUTPUT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"algorithm={payload['algorithm']}")
    print(f"input={payload['input_matrix']}")
    print(f"n={payload['n']}")
    print(f"root_city={payload['root_city']}")
    print(f"iterations_run={payload['iteration_count']}")
    print(f"best_iteration={payload['best_iteration']}")
    print(f"lower_bound={payload['lower_bound']:.12f}")
    print(f"previous_lower_bound={payload['previous_lower_bound']:.12f}")
    print(f"upper_bound={payload['upper_bound']}")
    typed_payload = cast(dict[str, Any], payload)
    absolute_gap = float(typed_payload["absolute_gap"])
    relative_gap_to_lower = float(typed_payload["relative_gap_to_lower"])
    relative_gap_to_upper = float(typed_payload["relative_gap_to_upper"])
    runtime_seconds = float(typed_payload["runtime_seconds"])
    print(f"absolute_gap={absolute_gap:.12f}")
    print(f"relative_gap_to_lower={relative_gap_to_lower * 100:.12f}%")
    print(f"relative_gap_to_upper={relative_gap_to_upper * 100:.12f}%")
    print(f"runtime_seconds={runtime_seconds:.3f}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
