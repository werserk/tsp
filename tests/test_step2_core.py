from __future__ import annotations

from pathlib import Path

import pytest

from src.io.matrix_loader import load_matrix
from src.io.validation import validate_matrix, validate_tour
from src.tsp.tour import tour_length


def test_loads_plain_matrix_with_declared_size(tmp_path: Path):
    matrix_file = tmp_path / "matrix.txt"
    matrix_file.write_text("3\n0 2 9\n2 0 4\n9 4 0\n", encoding="utf-8")

    data = load_matrix(matrix_file)

    assert data.n == 3
    assert data.format == "plain_with_size"
    assert data.matrix == [[0, 2, 9], [2, 0, 4], [9, 4, 0]]
    assert data.source_path == matrix_file


def test_loads_python_literal_matrix_assignment(tmp_path: Path):
    matrix_file = tmp_path / "matrix_literal.txt"
    matrix_file.write_text("M=[[0, 7], [7, 0]]\n", encoding="utf-8")

    data = load_matrix(matrix_file)

    assert data.n == 2
    assert data.format == "python_literal"
    assert data.matrix == [[0, 7], [7, 0]]


def test_matrix_validation_rejects_non_square_matrix():
    with pytest.raises(ValueError, match="square"):
        validate_matrix([[0, 1, 2], [1, 0]])


def test_matrix_validation_rejects_negative_distance():
    with pytest.raises(ValueError, match="negative"):
        validate_matrix([[0, -1], [-1, 0]])


def test_matrix_validation_rejects_nonzero_diagonal():
    with pytest.raises(ValueError, match="diagonal"):
        validate_matrix([[1, 2], [2, 0]])


def test_matrix_validation_rejects_asymmetric_matrix_by_default():
    with pytest.raises(ValueError, match="symmetric"):
        validate_matrix([[0, 2], [3, 0]])


def test_validate_tour_accepts_permutation_without_repeated_start():
    validate_tour([2, 0, 1], 3)


def test_validate_tour_rejects_duplicate_city():
    with pytest.raises(ValueError, match="exactly once"):
        validate_tour([0, 1, 1], 3)


def test_validate_tour_rejects_out_of_range_city():
    with pytest.raises(ValueError, match="out of range"):
        validate_tour([0, 1, 3], 3)


def test_tour_length_closes_cycle_without_repeated_start():
    matrix = [
        [0, 2, 9, 10],
        [2, 0, 6, 4],
        [9, 6, 0, 8],
        [10, 4, 8, 0],
    ]

    assert tour_length(matrix, [0, 1, 3, 2]) == 2 + 4 + 8 + 9


def test_tour_length_rejects_invalid_tour_before_counting():
    matrix = [[0, 1], [1, 0]]

    with pytest.raises(ValueError, match="exactly once"):
        tour_length(matrix, [0, 0])
