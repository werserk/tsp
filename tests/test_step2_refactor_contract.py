from __future__ import annotations

from pathlib import Path

import pytest

from experiments.step2_smoke_checks import SMOKE_CASES, MatrixSmokeCase, run_smoke_case
from src.io.exceptions import MatrixParseError, MatrixValidationError, TourValidationError
from src.io.matrix_loader import detect_matrix_format, load_matrix
from src.io.validation import validate_matrix, validate_tour
from src.tsp.constants import (
    CHALLENGE_CITY_COUNT,
    CHALLENGE_MATRIX_PATH,
    LECTURE_SAMPLE_CITY_COUNT,
    LECTURE_SAMPLE_MATRIX_PATH,
    MATRIX_FORMAT_PLAIN_WITH_SIZE,
    MATRIX_FORMAT_PYTHON_LITERAL,
)
from src.tsp.tour import tour_length


def test_project_constants_name_canonical_inputs():
    assert CHALLENGE_CITY_COUNT == 1114
    assert CHALLENGE_MATRIX_PATH == Path("data/raw/matrices/M.txt")
    assert LECTURE_SAMPLE_CITY_COUNT == 94
    assert LECTURE_SAMPLE_MATRIX_PATH == Path("data/raw/matrices/tsp_matrix1.txt")


def test_matrix_format_detection_uses_named_formats():
    assert detect_matrix_format("3\n0 1 2\n1 0 3\n2 3 0\n") == MATRIX_FORMAT_PLAIN_WITH_SIZE
    assert detect_matrix_format("M=[[0, 1], [1, 0]]") == MATRIX_FORMAT_PYTHON_LITERAL
    assert detect_matrix_format("[[0, 1], [1, 0]]") == MATRIX_FORMAT_PYTHON_LITERAL


def test_load_matrix_raises_parse_error_for_empty_file(tmp_path: Path):
    matrix_file = tmp_path / "empty.txt"
    matrix_file.write_text("\n", encoding="utf-8")

    with pytest.raises(MatrixParseError):
        load_matrix(matrix_file)


def test_validate_matrix_raises_matrix_validation_error():
    with pytest.raises(MatrixValidationError):
        validate_matrix([[0, 1], [2, 0]])


def test_validate_tour_raises_tour_validation_error():
    with pytest.raises(TourValidationError):
        validate_tour([0, 0], 2)


def test_tour_length_can_skip_matrix_validation_for_hot_paths():
    asymmetric_matrix = [[0, 1], [2, 0]]

    assert tour_length(asymmetric_matrix, [0, 1], validate=False) == 3
    with pytest.raises(MatrixValidationError):
        tour_length(asymmetric_matrix, [0, 1], validate=True)


def test_smoke_cases_are_named_dataclasses_and_use_constants():
    assert SMOKE_CASES == (
        MatrixSmokeCase(CHALLENGE_MATRIX_PATH, CHALLENGE_CITY_COUNT),
        MatrixSmokeCase(LECTURE_SAMPLE_MATRIX_PATH, LECTURE_SAMPLE_CITY_COUNT),
    )


def test_run_smoke_case_reports_named_format(tmp_path: Path):
    matrix_file = tmp_path / "matrix.txt"
    matrix_file.write_text("2\n0 5\n5 0\n", encoding="utf-8")

    report = run_smoke_case(MatrixSmokeCase(matrix_file, 2), root=Path("."))

    assert report == {
        "file": str(matrix_file),
        "format": MATRIX_FORMAT_PLAIN_WITH_SIZE,
        "n": 2,
        "sequential_tour_length": 10,
    }
