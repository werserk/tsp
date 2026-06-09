from __future__ import annotations

import json
from pathlib import Path

from src.heuristics.two_opt import (
    TWO_OPT_FIRST_IMPROVEMENT_ALGORITHM,
    TwoOptResult,
    apply_two_opt_move,
    improve_tour_two_opt,
    save_two_opt_result,
    two_opt_delta,
    two_opt_payload,
)
from src.tsp.tour import tour_length


def test_two_opt_delta_matches_independent_recalculation():
    matrix = [
        [0, 1, 10, 1],
        [1, 0, 1, 10],
        [10, 1, 0, 1],
        [1, 10, 1, 0],
    ]
    tour = [0, 1, 3, 2]

    delta = two_opt_delta(matrix, tour, i=2, k=3)
    moved = apply_two_opt_move(tour, i=2, k=3)

    assert delta == tour_length(matrix, moved) - tour_length(matrix, tour)
    assert delta == -18
    assert moved == [0, 1, 2, 3]


def test_two_opt_first_improvement_reduces_crossed_tour():
    matrix = [
        [0, 1, 10, 1],
        [1, 0, 1, 10],
        [10, 1, 0, 1],
        [1, 10, 1, 0],
    ]
    initial_tour = [0, 1, 3, 2]

    result = improve_tour_two_opt(matrix, initial_tour)

    assert result == TwoOptResult(
        algorithm=TWO_OPT_FIRST_IMPROVEMENT_ALGORITHM,
        initial_length=22,
        length=4,
        tour=[0, 1, 2, 3],
        moves_applied=1,
        passes=2,
        metadata={"strategy": "first_improvement"},
    )
    assert tour_length(matrix, result.tour, validate=True) == result.length


def test_two_opt_keeps_tour_when_no_improving_move_exists():
    matrix = [
        [0, 1, 2],
        [1, 0, 1],
        [2, 1, 0],
    ]
    initial_tour = [0, 1, 2]

    result = improve_tour_two_opt(matrix, initial_tour)

    assert result.tour == initial_tour
    assert result.length == tour_length(matrix, initial_tour)
    assert result.moves_applied == 0


def test_two_opt_payload_records_improvement_metadata():
    result = TwoOptResult(
        algorithm=TWO_OPT_FIRST_IMPROVEMENT_ALGORITHM,
        initial_length=100,
        length=80,
        tour=[0, 1, 2],
        moves_applied=7,
        passes=3,
        metadata={"strategy": "first_improvement"},
    )

    payload = two_opt_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        source_artifact=Path("results/best/step3-nearest-neighbor-best.json"),
        n=3,
        command="cmd",
    )

    assert payload["algorithm"] == TWO_OPT_FIRST_IMPROVEMENT_ALGORITHM
    assert payload["input_file"] == "data/raw/matrices/M.txt"
    assert payload["source_artifact"] == "results/best/step3-nearest-neighbor-best.json"
    assert payload["n"] == 3
    assert payload["initial_length"] == 100
    assert payload["length"] == 80
    assert payload["improvement"] == 20
    assert payload["moves_applied"] == 7
    assert payload["passes"] == 3
    assert payload["tour"] == [0, 1, 2]
    assert payload["command"] == "cmd"
    assert "created_at" in payload


def test_save_two_opt_result_writes_json(tmp_path: Path):
    result = TwoOptResult(
        algorithm=TWO_OPT_FIRST_IMPROVEMENT_ALGORITHM,
        initial_length=100,
        length=80,
        tour=[0, 1, 2],
        moves_applied=7,
        passes=3,
        metadata={"strategy": "first_improvement"},
    )
    output_path = tmp_path / "two-opt.json"

    save_two_opt_result(
        result,
        output_path=output_path,
        input_file=Path("data/raw/matrices/M.txt"),
        source_artifact=Path("source.json"),
        n=3,
        command="cmd",
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["length"] == 80
    assert payload["improvement"] == 20
    assert output_path.read_text(encoding="utf-8").endswith("\n")
