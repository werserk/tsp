from __future__ import annotations

from src.io.validation import validate_matrix, validate_tour


Matrix = list[list[int]]


def tour_length(matrix: Matrix, tour: list[int]) -> int:
    """Return length of a Hamiltonian cycle; final edge to start is implicit."""

    validate_matrix(matrix)
    n = len(matrix)
    validate_tour(tour, n)

    total = 0
    for idx, city in enumerate(tour):
        next_city = tour[(idx + 1) % n]
        total += matrix[city][next_city]
    return total
