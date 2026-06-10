from __future__ import annotations

import json
from pathlib import Path

from src.bounds.held_karp import adjusted_one_tree_lower_bound
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "results/best/step13-held-karp-decay-099-lower-bound.json"
PREVIOUS_BEST = 65493.4373688764
UPPER_BOUND = 73934


def test_step13_artifact_is_strict_verified_lower_bound() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)

    recomputed = adjusted_one_tree_lower_bound(
        data.matrix,
        root_city=int(payload["root_city"]),
        penalties=[float(value) for value in payload["best_penalties"]],
    )

    lower_bound = float(payload["lower_bound"])
    assert payload["type"] == "lower_bound"
    assert lower_bound > PREVIOUS_BEST
    assert lower_bound <= UPPER_BOUND
    assert abs(recomputed.lower_bound - lower_bound) < 1e-7
    assert payload["verification"]["strict_improvement"] is True
    assert payload["verification"]["lower_bound_le_upper_bound"] is True


def test_step13_gap_fields_match_current_bounds() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    lower_bound = float(payload["lower_bound"])
    absolute_gap = UPPER_BOUND - lower_bound

    assert payload["upper_bound"] == UPPER_BOUND
    assert payload["absolute_gap"] == absolute_gap
    assert payload["relative_gap_to_lower"] == absolute_gap / lower_bound
    assert payload["relative_gap_to_upper"] == absolute_gap / UPPER_BOUND
    assert payload["integer_lower_bound"] == 72712
