from __future__ import annotations

from src.io.validation import validate_matrix, validate_tour
from src.tsp.types import Matrix, Tour


def tour_length(matrix: Matrix, tour: Tour, *, validate: bool = True) -> int:
    """Return length of a Hamiltonian cycle; final edge to start is implicit."""

    if validate:
        validate_matrix(matrix)
        validate_tour(tour, len(matrix))

    return sum(
        matrix[city][tour[(index + 1) % len(tour)]]
        for index, city in enumerate(tour)
    )
