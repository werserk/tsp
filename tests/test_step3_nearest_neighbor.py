from __future__ import annotations

import json
from pathlib import Path

from src.heuristics.nearest_neighbor import (
    NEAREST_NEIGHBOR_MULTI_START_ALGORITHM,
    TourResult,
    multi_start_nearest_neighbor,
    nearest_neighbor_tour,
    result_to_json_payload,
    save_tour_result,
)
from src.io.validation import validate_tour
from src.tsp.tour import tour_length


def test_nearest_neighbor_builds_valid_tour_with_deterministic_tie_breaking():
    matrix = [
        [0, 2, 2, 9],
        [2, 0, 1, 3],
        [2, 1, 0, 4],
        [9, 3, 4, 0],
    ]

    tour = nearest_neighbor_tour(matrix, start_city=0)

    assert tour == [0, 1, 2, 3]
    validate_tour(tour, len(matrix))
    assert tour_length(matrix, tour) == 16


def test_multi_start_nearest_neighbor_returns_best_independently_recomputed_result():
    matrix = [
        [0, 1, 9, 9],
        [1, 0, 2, 2],
        [9, 2, 0, 1],
        [9, 2, 1, 0],
    ]

    result = multi_start_nearest_neighbor(matrix, starts=[0, 1, 2, 3])

    assert result == TourResult(
        algorithm=NEAREST_NEIGHBOR_MULTI_START_ALGORITHM,
        tour=[0, 1, 2, 3],
        length=13,
        start_city=0,
        metadata={"starts_checked": 4},
    )
    assert tour_length(matrix, result.tour, validate=True) == result.length


def test_result_payload_contains_reproducible_upper_bound_metadata():
    result = TourResult(
        algorithm=NEAREST_NEIGHBOR_MULTI_START_ALGORITHM,
        tour=[0, 1, 2],
        length=17,
        start_city=0,
        metadata={"starts_checked": 3},
    )

    payload = result_to_json_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        n=3,
        command="python experiments/step3_nearest_neighbor_baseline.py",
    )

    assert payload["algorithm"] == NEAREST_NEIGHBOR_MULTI_START_ALGORITHM
    assert payload["input_file"] == "data/raw/matrices/M.txt"
    assert payload["n"] == 3
    assert payload["length"] == 17
    assert payload["start_city"] == 0
    assert payload["tour"] == [0, 1, 2]
    assert payload["metadata"]["starts_checked"] == 3
    assert payload["command"] == "python experiments/step3_nearest_neighbor_baseline.py"
    assert "created_at" in payload


def test_save_tour_result_writes_stable_json(tmp_path: Path):
    result = TourResult(
        algorithm=NEAREST_NEIGHBOR_MULTI_START_ALGORITHM,
        tour=[0, 1, 2],
        length=17,
        start_city=0,
        metadata={"starts_checked": 3},
    )
    output_path = tmp_path / "best.json"

    save_tour_result(
        result,
        output_path=output_path,
        input_file=Path("data/raw/matrices/M.txt"),
        n=3,
        command="cmd",
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["length"] == 17
    assert payload["tour"] == [0, 1, 2]
    assert output_path.read_text(encoding="utf-8").endswith("\n")
