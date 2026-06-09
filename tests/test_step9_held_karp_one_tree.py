from __future__ import annotations

from pathlib import Path

from src.bounds.held_karp import (
    HELD_KARP_ONE_TREE_ALGORITHM,
    HeldKarpIteration,
    HeldKarpOneTreeResult,
    adjusted_one_tree_lower_bound,
    held_karp_one_tree_payload,
    optimize_held_karp_one_tree,
    subgradient_update,
)


def test_adjusted_one_tree_bound_uses_lagrangian_correction_and_records_degrees():
    matrix = [
        [0, 10, 10, 10],
        [10, 0, 1, 4],
        [10, 1, 0, 2],
        [10, 4, 2, 0],
    ]

    result = adjusted_one_tree_lower_bound(matrix, root_city=0, penalties=[0.0, 5.0, 0.0, 0.0])

    assert result.adjusted_weight == 28.0
    assert result.lower_bound == 18.0
    assert result.degrees == [2, 1, 3, 2]
    assert result.root_edges == [(0, 2, 10.0), (0, 3, 10.0)]
    assert result.tree_edges == [(1, 2, 6.0), (2, 3, 2.0)]
    assert result.metadata["proof"] == "lagrangian_one_tree_bound"


def test_subgradient_update_moves_penalties_by_degree_deficit():
    updated = subgradient_update(
        penalties=[0.0, 5.0, 0.0, 0.0],
        degrees=[2, 1, 3, 2],
        step_size=0.5,
    )

    assert updated == [0.0, 4.5, 0.5, 0.0]


def test_optimize_held_karp_one_tree_keeps_best_seen_bound_and_iteration_trace():
    matrix = [
        [0, 10, 10, 10],
        [10, 0, 1, 4],
        [10, 1, 0, 2],
        [10, 4, 2, 0],
    ]

    result = optimize_held_karp_one_tree(
        matrix,
        root_city=0,
        iterations=3,
        initial_step_size=1.0,
        step_decay=0.5,
    )

    assert result.algorithm == HELD_KARP_ONE_TREE_ALGORITHM
    assert result.root_city == 0
    assert 1 <= result.iteration_count <= 3
    assert len(result.iterations) == result.iteration_count
    assert result.best_lower_bound >= result.iterations[0].lower_bound
    assert result.best_iteration in [item.iteration for item in result.iterations]
    assert result.metadata["proof"] == "max_of_lagrangian_one_tree_bounds"


def test_held_karp_payload_records_parameters_gap_and_best_iteration():
    result = HeldKarpOneTreeResult(
        algorithm=HELD_KARP_ONE_TREE_ALGORITHM,
        root_city=0,
        best_lower_bound=24.5,
        best_iteration=2,
        iteration_count=3,
        iterations=[
            HeldKarpIteration(iteration=0, step_size=1.0, lower_bound=23.0, adjusted_weight=23.0, degrees=[2, 2, 3, 1], penalties=[0.0, 0.0, 0.0, 0.0]),
            HeldKarpIteration(iteration=1, step_size=0.5, lower_bound=24.5, adjusted_weight=24.5, degrees=[2, 2, 2, 2], penalties=[0.0, 0.0, 1.0, -1.0]),
        ],
        best_penalties=[0.0, 0.0, 1.0, -1.0],
        metadata={"proof": "max_of_lagrangian_one_tree_bounds"},
    )

    payload = held_karp_one_tree_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        n=4,
        upper_bound=30,
        upper_bound_artifact=Path("results/best/step6-lkh-best.json"),
        previous_lower_bound_artifact=Path("results/best/step7-several-root-one-tree.json"),
        proof_note=Path("notes/11-step9-held-karp-one-tree.md"),
        command="cmd",
        parameters={"iterations": 3, "initial_step_size": 1.0, "step_decay": 0.5},
    )

    assert payload["algorithm"] == HELD_KARP_ONE_TREE_ALGORITHM
    assert payload["lower_bound"] == 24.5
    assert payload["upper_bound"] == 30
    assert payload["absolute_gap"] == 5.5
    assert payload["relative_gap"] == 5.5 / 30
    assert payload["best_iteration"] == 2
    assert payload["parameters"]["iterations"] == 3
    assert payload["previous_lower_bound_artifact"] == "results/best/step7-several-root-one-tree.json"
    assert "penalties" not in payload["iterations"][0]
    assert "degrees" not in payload["iterations"][0]
    assert payload["iterations"][0]["degree_violation_l1"] == 2
    assert "created_at" in payload
