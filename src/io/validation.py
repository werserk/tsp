from __future__ import annotations


Matrix = list[list[int]]


def validate_matrix(matrix: Matrix, *, symmetric: bool = True) -> None:
    """Validate core assumptions for a TSP distance matrix."""

    n = len(matrix)
    if n == 0:
        raise ValueError("matrix must be non-empty and square")

    for i, row in enumerate(matrix):
        if len(row) != n:
            raise ValueError(
                f"matrix must be square: row {i} has length {len(row)}, expected {n}"
            )
        for j, value in enumerate(row):
            if value < 0:
                raise ValueError(f"matrix contains negative distance at ({i}, {j})")
            if i == j and value != 0:
                raise ValueError(f"matrix diagonal must be zero at ({i}, {j})")

    if symmetric:
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i][j] != matrix[j][i]:
                    raise ValueError(
                        "matrix must be symmetric: "
                        f"d({i}, {j})={matrix[i][j]} != d({j}, {i})={matrix[j][i]}"
                    )


def validate_tour(tour: list[int], n: int) -> None:
    """Validate tour format: each city 0..n-1 appears exactly once.

    The return edge to the start is implicit and must not be repeated in `tour`.
    """

    if n <= 0:
        raise ValueError("n must be positive")
    if len(tour) != n:
        raise ValueError(f"tour must visit each city exactly once: got {len(tour)}, expected {n}")

    seen = set()
    for city in tour:
        if city < 0 or city >= n:
            raise ValueError(f"tour city out of range: {city}, expected 0..{n - 1}")
        if city in seen:
            raise ValueError(f"tour must visit each city exactly once: duplicate city {city}")
        seen.add(city)

    if len(seen) != n:
        raise ValueError("tour must visit each city exactly once")
