from __future__ import annotations

from dataclasses import dataclass

from src.io.validation import validate_matrix
from src.tsp.types import City, Matrix

MST_ALGORITHM = "minimum_spanning_tree"


@dataclass(frozen=True)
class MSTResult:
    algorithm: str
    weight: int
    edges: list[tuple[City, City, int]]
    vertices: list[City]


def minimum_spanning_tree(matrix: Matrix, *, excluded_vertex: City | None = None) -> MSTResult:
    """Return a deterministic Prim MST, optionally excluding one vertex."""

    validate_matrix(matrix)
    vertices = [city for city in range(len(matrix)) if city != excluded_vertex]
    if not vertices:
        raise ValueError("MST requires at least one included vertex")
    if len(vertices) == 1:
        return MSTResult(algorithm=MST_ALGORITHM, weight=0, edges=[], vertices=vertices)

    included = {vertices[0]}
    edges: list[tuple[City, City, int]] = []
    total_weight = 0

    while len(included) < len(vertices):
        next_edge = _find_lightest_crossing_edge(matrix, included, vertices)
        from_city, to_city, weight = next_edge
        included.add(to_city)
        edges.append(next_edge)
        total_weight += weight

    return MSTResult(
        algorithm=MST_ALGORITHM,
        weight=total_weight,
        edges=edges,
        vertices=vertices,
    )


def _find_lightest_crossing_edge(
    matrix: Matrix,
    included: set[City],
    vertices: list[City],
) -> tuple[City, City, int]:
    best: tuple[City, City, int] | None = None
    for from_city in sorted(included):
        for to_city in vertices:
            if to_city in included:
                continue
            candidate = (from_city, to_city, matrix[from_city][to_city])
            if best is None or _edge_sort_key(candidate) < _edge_sort_key(best):
                best = candidate

    if best is None:
        raise ValueError("graph is disconnected")
    return best


def _edge_sort_key(edge: tuple[City, City, int]) -> tuple[int, City, City]:
    from_city, to_city, weight = edge
    return weight, from_city, to_city
