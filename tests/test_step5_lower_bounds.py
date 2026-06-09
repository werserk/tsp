from __future__ import annotations

import json
from pathlib import Path

from src.bounds.mst import MST_ALGORITHM, MSTResult, minimum_spanning_tree
from src.bounds.one_tree import (
    ONE_TREE_LOWER_BOUND_ALGORITHM,
    OneTreeResult,
    one_tree_lower_bound,
    one_tree_payload,
    save_one_tree_result,
    two_cheapest_incident_edges,
)


def test_minimum_spanning_tree_returns_weight_and_edges():
    matrix = [
        [0, 1, 4, 3],
        [1, 0, 2, 5],
        [4, 2, 0, 1],
        [3, 5, 1, 0],
    ]

    result = minimum_spanning_tree(matrix)

    assert result == MSTResult(
        algorithm=MST_ALGORITHM,
        weight=4,
        edges=[(0, 1, 1), (1, 2, 2), (2, 3, 1)],
        vertices=[0, 1, 2, 3],
    )


def test_minimum_spanning_tree_can_exclude_root_for_one_tree():
    matrix = [
        [0, 1, 4, 3],
        [1, 0, 2, 5],
        [4, 2, 0, 1],
        [3, 5, 1, 0],
    ]

    result = minimum_spanning_tree(matrix, excluded_vertex=0)

    assert result.weight == 3
    assert result.edges == [(1, 2, 2), (2, 3, 1)]
    assert result.vertices == [1, 2, 3]


def test_two_cheapest_incident_edges_are_deterministic():
    matrix = [
        [0, 1, 1, 5],
        [1, 0, 2, 3],
        [1, 2, 0, 4],
        [5, 3, 4, 0],
    ]

    assert two_cheapest_incident_edges(matrix, root_city=0) == [(0, 1, 1), (0, 2, 1)]


def test_one_tree_lower_bound_combines_mst_without_root_and_two_root_edges():
    matrix = [
        [0, 1, 4, 3],
        [1, 0, 2, 5],
        [4, 2, 0, 1],
        [3, 5, 1, 0],
    ]

    result = one_tree_lower_bound(matrix, root_city=0)

    assert result == OneTreeResult(
        algorithm=ONE_TREE_LOWER_BOUND_ALGORITHM,
        root_city=0,
        mst_without_root_weight=3,
        root_edges=[(0, 1, 1), (0, 3, 3)],
        lower_bound=7,
        metadata={"proof": "mst_without_root_plus_two_cheapest_root_edges"},
    )


def test_one_tree_payload_records_gap_to_upper_bound():
    result = OneTreeResult(
        algorithm=ONE_TREE_LOWER_BOUND_ALGORITHM,
        root_city=0,
        mst_without_root_weight=3,
        root_edges=[(0, 1, 1), (0, 3, 3)],
        lower_bound=7,
        metadata={"proof": "mst_without_root_plus_two_cheapest_root_edges"},
    )

    payload = one_tree_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        n=4,
        upper_bound=20,
        upper_bound_artifact=Path("results/best/step4-two-opt-best.json"),
        proof_note=Path("notes/06-step5-lower-bound-mst-one-tree.md"),
        command="cmd",
    )

    assert payload["algorithm"] == ONE_TREE_LOWER_BOUND_ALGORITHM
    assert payload["input_file"] == "data/raw/matrices/M.txt"
    assert payload["n"] == 4
    assert payload["root_city"] == 0
    assert payload["mst_without_root_weight"] == 3
    assert payload["two_cheapest_root_edges"] == [(0, 1, 1), (0, 3, 3)]
    assert payload["lower_bound"] == 7
    assert payload["upper_bound"] == 20
    assert payload["absolute_gap"] == 13
    assert payload["relative_gap"] == 0.65
    assert payload["upper_bound_artifact"] == "results/best/step4-two-opt-best.json"
    assert payload["proof_note"] == "notes/06-step5-lower-bound-mst-one-tree.md"
    assert payload["command"] == "cmd"
    assert "created_at" in payload


def test_save_one_tree_result_writes_json(tmp_path: Path):
    result = OneTreeResult(
        algorithm=ONE_TREE_LOWER_BOUND_ALGORITHM,
        root_city=0,
        mst_without_root_weight=3,
        root_edges=[(0, 1, 1), (0, 3, 3)],
        lower_bound=7,
        metadata={"proof": "mst_without_root_plus_two_cheapest_root_edges"},
    )
    output_path = tmp_path / "lower-bound.json"

    save_one_tree_result(
        result,
        output_path=output_path,
        input_file=Path("data/raw/matrices/M.txt"),
        n=4,
        upper_bound=20,
        upper_bound_artifact=Path("upper.json"),
        proof_note=Path("proof.md"),
        command="cmd",
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["lower_bound"] == 7
    assert payload["absolute_gap"] == 13
    assert output_path.read_text(encoding="utf-8").endswith("\n")
