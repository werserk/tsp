from __future__ import annotations

import json
from pathlib import Path

from src.heuristics.multistart_two_opt import (
    MULTISTART_NN_TWO_OPT_ALGORITHM,
    MultiStartTwoOptResult,
    multistart_nearest_neighbor_two_opt,
    multistart_two_opt_payload,
    save_multistart_two_opt_result,
)
from src.tsp.tour import tour_length


def test_multistart_nearest_neighbor_two_opt_returns_best_improved_tour():
    matrix = [
        [0, 1, 10, 1],
        [1, 0, 1, 10],
        [10, 1, 0, 1],
        [1, 10, 1, 0],
    ]

    result = multistart_nearest_neighbor_two_opt(matrix, starts=[0, 2])

    assert result.algorithm == MULTISTART_NN_TWO_OPT_ALGORITHM
    assert result.length == 4
    assert result.length == tour_length(matrix, result.tour, validate=True)
    assert result.starts_checked == 2
    assert result.best_start_city in {0, 2}
    assert result.metadata["strategy"] == "nearest_neighbor_then_two_opt"
    assert result.metadata["two_opt_strategy"] == "first_improvement"
    assert result.metadata["best_initial_length"] >= result.length


def test_multistart_nearest_neighbor_two_opt_rejects_empty_starts():
    matrix = [
        [0, 1, 2],
        [1, 0, 1],
        [2, 1, 0],
    ]

    try:
        multistart_nearest_neighbor_two_opt(matrix, starts=[])
    except ValueError as exc:
        assert "at least one start city" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_multistart_two_opt_payload_records_source_and_gap_metadata():
    result = MultiStartTwoOptResult(
        algorithm=MULTISTART_NN_TWO_OPT_ALGORITHM,
        length=90,
        tour=[0, 1, 2],
        best_start_city=1,
        best_initial_length=120,
        starts_checked=3,
        total_two_opt_moves=10,
        metadata={"strategy": "nearest_neighbor_then_two_opt"},
    )

    payload = multistart_two_opt_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        n=3,
        command="cmd",
        current_best_upper_bound=100,
        lower_bound=60,
    )

    assert payload["algorithm"] == MULTISTART_NN_TWO_OPT_ALGORITHM
    assert payload["input_file"] == "data/raw/matrices/M.txt"
    assert payload["n"] == 3
    assert payload["length"] == 90
    assert payload["previous_upper_bound"] == 100
    assert payload["improvement_over_previous_upper_bound"] == 10
    assert payload["lower_bound"] == 60
    assert payload["absolute_gap"] == 30
    assert payload["relative_gap"] == 30 / 90
    assert payload["best_start_city"] == 1
    assert payload["best_initial_length"] == 120
    assert payload["starts_checked"] == 3
    assert payload["total_two_opt_moves"] == 10
    assert payload["tour"] == [0, 1, 2]
    assert payload["command"] == "cmd"
    assert "created_at" in payload


def test_save_multistart_two_opt_result_writes_json(tmp_path: Path):
    result = MultiStartTwoOptResult(
        algorithm=MULTISTART_NN_TWO_OPT_ALGORITHM,
        length=90,
        tour=[0, 1, 2],
        best_start_city=1,
        best_initial_length=120,
        starts_checked=3,
        total_two_opt_moves=10,
        metadata={"strategy": "nearest_neighbor_then_two_opt"},
    )
    output_path = tmp_path / "multistart-two-opt.json"

    save_multistart_two_opt_result(
        result,
        output_path=output_path,
        input_file=Path("data/raw/matrices/M.txt"),
        n=3,
        command="cmd",
        current_best_upper_bound=100,
        lower_bound=60,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["length"] == 90
    assert payload["absolute_gap"] == 30
    assert output_path.read_text(encoding="utf-8").endswith("\n")
