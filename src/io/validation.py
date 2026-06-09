from __future__ import annotations

from src.io.exceptions import MatrixValidationError, TourValidationError
from src.tsp.types import Matrix, Tour


def validate_matrix(matrix: Matrix, *, symmetric: bool = True) -> None:
    """Validate core assumptions for a TSP distance matrix."""

    _validate_non_empty(matrix)
    _validate_square(matrix)
    _validate_non_negative_and_zero_diagonal(matrix)
    if symmetric:
        _validate_symmetric(matrix)


def _validate_non_empty(matrix: Matrix) -> None:
    if len(matrix) == 0:
        raise MatrixValidationError("matrix must be non-empty and square")


def _validate_square(matrix: Matrix) -> None:
    n = len(matrix)
    for row_index, row in enumerate(matrix):
        if len(row) != n:
            raise MatrixValidationError(
                "matrix must be square: "
                f"row {row_index} has length {len(row)}, expected {n}"
            )


def _validate_non_negative_and_zero_diagonal(matrix: Matrix) -> None:
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            if value < 0:
                raise MatrixValidationError(
                    f"matrix contains negative distance at ({row_index}, {column_index})"
                )
            if row_index == column_index and value != 0:
                raise MatrixValidationError(
                    f"matrix diagonal must be zero at ({row_index}, {column_index})"
                )


def _validate_symmetric(matrix: Matrix) -> None:
    n = len(matrix)
    for row_index in range(n):
        for column_index in range(row_index + 1, n):
            left = matrix[row_index][column_index]
            right = matrix[column_index][row_index]
            if left != right:
                raise MatrixValidationError(
                    "matrix must be symmetric: "
                    f"d({row_index}, {column_index})={left} "
                    f"!= d({column_index}, {row_index})={right}"
                )


def validate_tour(tour: Tour, n: int) -> None:
    """Validate tour format: each city 0..n-1 appears exactly once.

    The return edge to the start is implicit and must not be repeated in `tour`.
    """

    _validate_positive_city_count(n)
    _validate_tour_length(tour, n)
    _validate_tour_city_range_and_uniqueness(tour, n)


def _validate_positive_city_count(n: int) -> None:
    if n <= 0:
        raise TourValidationError("n must be positive")


def _validate_tour_length(tour: Tour, n: int) -> None:
    if len(tour) != n:
        raise TourValidationError(
            f"tour must visit each city exactly once: got {len(tour)}, expected {n}"
        )


def _validate_tour_city_range_and_uniqueness(tour: Tour, n: int) -> None:
    seen: set[int] = set()
    for city in tour:
        if city < 0 or city >= n:
            raise TourValidationError(f"tour city out of range: {city}, expected 0..{n - 1}")
        if city in seen:
            raise TourValidationError(
                f"tour must visit each city exactly once: duplicate city {city}"
            )
        seen.add(city)
