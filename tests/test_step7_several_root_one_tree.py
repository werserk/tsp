from __future__ import annotations

from pathlib import Path

from src.bounds.one_tree import (
    SEVERAL_ROOT_ONE_TREE_ALGORITHM,
    SeveralRootOneTreeResult,
    best_one_tree_lower_bound,
    several_root_one_tree_payload,
)


def test_best_one_tree_lower_bound_selects_strongest_candidate_root():
    matrix = [
        [0, 1, 1, 9, 9],
        [1, 0, 1, 9, 9],
        [1, 1, 0, 9, 9],
        [9, 9, 9, 0, 1],
        [9, 9, 9, 1, 0],
    ]

    result = best_one_tree_lower_bound(matrix, candidate_roots=[0, 3, 4])

    assert result == SeveralRootOneTreeResult(
        algorithm=SEVERAL_ROOT_ONE_TREE_ALGORITHM,
        candidate_roots=[0, 3, 4],
        best_root_city=3,
        lower_bound=21,
        evaluated_bounds=[
            {"root_city": 0, "lower_bound": 13},
            {"root_city": 3, "lower_bound": 21},
            {"root_city": 4, "lower_bound": 21},
        ],
        metadata={"proof": "max_of_valid_fixed_root_one_tree_lower_bounds"},
    )


def test_best_one_tree_lower_bound_defaults_to_all_roots():
    matrix = [
        [0, 1, 1, 9, 9],
        [1, 0, 1, 9, 9],
        [1, 1, 0, 9, 9],
        [9, 9, 9, 0, 1],
        [9, 9, 9, 1, 0],
    ]

    result = best_one_tree_lower_bound(matrix)

    assert result.candidate_roots == [0, 1, 2, 3, 4]
    assert result.best_root_city == 3
    assert result.lower_bound == 21


def test_several_root_one_tree_payload_records_gap_and_candidate_count():
    result = SeveralRootOneTreeResult(
        algorithm=SEVERAL_ROOT_ONE_TREE_ALGORITHM,
        candidate_roots=[0, 3, 4],
        best_root_city=3,
        lower_bound=21,
        evaluated_bounds=[
            {"root_city": 0, "lower_bound": 13},
            {"root_city": 3, "lower_bound": 21},
            {"root_city": 4, "lower_bound": 21},
        ],
        metadata={"proof": "max_of_valid_fixed_root_one_tree_lower_bounds"},
    )

    payload = several_root_one_tree_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        n=5,
        upper_bound=30,
        upper_bound_artifact=Path("results/best/step6-lkh-best.json"),
        proof_note=Path("notes/09-step7-several-root-one-tree.md"),
        command="cmd",
    )

    assert payload["algorithm"] == SEVERAL_ROOT_ONE_TREE_ALGORITHM
    assert payload["candidate_count"] == 3
    assert payload["best_root_city"] == 3
    assert payload["lower_bound"] == 21
    assert payload["upper_bound"] == 30
    assert payload["absolute_gap"] == 9
    assert payload["relative_gap"] == 0.3
    assert payload["upper_bound_artifact"] == "results/best/step6-lkh-best.json"
    assert payload["proof_note"] == "notes/09-step7-several-root-one-tree.md"
    assert payload["command"] == "cmd"
    assert "created_at" in payload
