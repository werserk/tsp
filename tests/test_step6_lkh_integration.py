from __future__ import annotations

import json
from pathlib import Path

from src.integrations.lkh import (
    LKH_ALGORITHM,
    LKHResult,
    export_tsplib_full_matrix,
    lkh_payload,
    parse_lkh_tour,
    save_lkh_result,
    write_lkh_parameter_file,
)


def test_export_tsplib_full_matrix_uses_explicit_full_matrix_format(tmp_path: Path):
    matrix = [
        [0, 2, 9],
        [2, 0, 4],
        [9, 4, 0],
    ]
    output_path = tmp_path / "case.tsp"

    export_tsplib_full_matrix(matrix, output_path=output_path, name="tiny")

    assert output_path.read_text(encoding="utf-8") == (
        "NAME: tiny\n"
        "TYPE: TSP\n"
        "DIMENSION: 3\n"
        "EDGE_WEIGHT_TYPE: EXPLICIT\n"
        "EDGE_WEIGHT_FORMAT: FULL_MATRIX\n"
        "EDGE_WEIGHT_SECTION\n"
        "0 2 9\n"
        "2 0 4\n"
        "9 4 0\n"
        "EOF\n"
    )


def test_write_lkh_parameter_file_records_problem_and_tour_paths(tmp_path: Path):
    problem = tmp_path / "case.tsp"
    output = tmp_path / "case.tour"
    par = tmp_path / "case.par"

    write_lkh_parameter_file(
        parameter_path=par,
        problem_file=problem,
        output_tour_file=output,
        runs=3,
        max_trials=100,
        seed=7,
    )

    assert par.read_text(encoding="utf-8") == (
        f"PROBLEM_FILE = {problem}\n"
        f"OUTPUT_TOUR_FILE = {output}\n"
        "RUNS = 3\n"
        "MAX_TRIALS = 100\n"
        "SEED = 7\n"
        "TRACE_LEVEL = 1\n"
    )


def test_parse_lkh_tour_converts_tsplib_one_based_tour_to_zero_based(tmp_path: Path):
    tour_file = tmp_path / "case.tour"
    tour_file.write_text(
        "NAME : tiny.opt.tour\n"
        "TYPE : TOUR\n"
        "DIMENSION : 4\n"
        "TOUR_SECTION\n"
        "1\n"
        "3\n"
        "4\n"
        "2\n"
        "-1\n"
        "EOF\n",
        encoding="utf-8",
    )

    assert parse_lkh_tour(tour_file) == [0, 2, 3, 1]


def test_lkh_payload_records_verified_length_and_gap():
    result = LKHResult(
        algorithm=LKH_ALGORITHM,
        tour=[0, 2, 1],
        length=17,
        metadata={"runs": 3, "max_trials": 100, "seed": 7},
    )

    payload = lkh_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        n=3,
        previous_upper_bound=20,
        lower_bound=10,
        command="cmd",
        lkh_binary=Path("tools/LKH"),
    )

    assert payload["algorithm"] == LKH_ALGORITHM
    assert payload["input_file"] == "data/raw/matrices/M.txt"
    assert payload["n"] == 3
    assert payload["length"] == 17
    assert payload["improvement_vs_previous_upper"] == 3
    assert payload["lower_bound"] == 10
    assert payload["absolute_gap"] == 7
    assert payload["relative_gap"] == 7 / 17
    assert payload["tour"] == [0, 2, 1]
    assert payload["metadata"] == {"runs": 3, "max_trials": 100, "seed": 7}
    assert payload["command"] == "cmd"
    assert payload["lkh_binary"] == "tools/LKH"
    assert "created_at" in payload


def test_save_lkh_result_writes_json(tmp_path: Path):
    result = LKHResult(
        algorithm=LKH_ALGORITHM,
        tour=[0, 2, 1],
        length=17,
        metadata={"runs": 3},
    )
    output_path = tmp_path / "lkh.json"

    save_lkh_result(
        result,
        output_path=output_path,
        input_file=Path("data/raw/matrices/M.txt"),
        n=3,
        previous_upper_bound=20,
        lower_bound=10,
        command="cmd",
        lkh_binary=Path("tools/LKH"),
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["length"] == 17
    assert output_path.read_text(encoding="utf-8").endswith("\n")
