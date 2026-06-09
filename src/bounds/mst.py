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

    start = vertices[0]
    included = {start}
    edges: list[tuple[City, City, int]] = []
    total_weight = 0
    best_crossing_edge: dict[City, tuple[City, City, int]] = {
        city: (start, city, matrix[start][city]) for city in vertices if city != start
    }

    while len(included) < len(vertices):
        next_edge = min(
            (edge for city, edge in best_crossing_edge.items() if city not in included),
            key=_edge_sort_key,
        )
        from_city, to_city, weight = next_edge
        included.add(to_city)
        edges.append(next_edge)
        total_weight += weight

        for city in vertices:
            if city in included:
                continue
            candidate = (to_city, city, matrix[to_city][city])
            if _edge_sort_key(candidate) < _edge_sort_key(best_crossing_edge[city]):
                best_crossing_edge[city] = candidate

    return MSTResult(
        algorithm=MST_ALGORITHM,
        weight=total_weight,
        edges=edges,
        vertices=vertices,
    )


def _edge_sort_key(edge: tuple[City, City, int]) -> tuple[int, City, City]:
    from_city, to_city, weight = edge
    return weight, from_city, to_city
