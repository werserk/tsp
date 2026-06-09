from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.io.validation import validate_matrix
from src.tsp.types import City, Matrix

HELD_KARP_ONE_TREE_ALGORITHM = "held_karp_lagrangian_one_tree_lower_bound"
LAGRANGIAN_ONE_TREE_PROOF = "lagrangian_one_tree_bound"
HELD_KARP_ONE_TREE_PROOF = "max_of_lagrangian_one_tree_bounds"


@dataclass(frozen=True)
class AdjustedOneTreeResult:
    root_city: City
    adjusted_weight: float
    lower_bound: float
    degrees: list[int]
    tree_edges: list[tuple[City, City, float]]
    root_edges: list[tuple[City, City, float]]
    penalties: list[float]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class HeldKarpIteration:
    iteration: int
    step_size: float
    lower_bound: float
    adjusted_weight: float
    degrees: list[int]
    penalties: list[float]


@dataclass(frozen=True)
class HeldKarpOneTreeResult:
    algorithm: str
    root_city: City
    best_lower_bound: float
    best_iteration: int
    iteration_count: int
    iterations: list[HeldKarpIteration]
    best_penalties: list[float]
    metadata: dict[str, Any]


def adjusted_one_tree_lower_bound(
    matrix: Matrix,
    *,
    root_city: City = 0,
    penalties: list[float] | None = None,
) -> AdjustedOneTreeResult:
    """Return a Lagrangian fixed-root 1-tree lower bound for given node penalties."""

    validate_matrix(matrix)
    n = len(matrix)
    _validate_root_city(n, root_city)
    node_penalties = [0.0] * n if penalties is None else [float(value) for value in penalties]
    if len(node_penalties) != n:
        raise ValueError(f"expected {n} penalties, got {len(node_penalties)}")

    tree_edges = _adjusted_mst_edges(matrix, root_city=root_city, penalties=node_penalties)
    root_edges = _two_cheapest_adjusted_root_edges(matrix, root_city=root_city, penalties=node_penalties)
    adjusted_weight = sum(weight for _, _, weight in tree_edges) + sum(
        weight for _, _, weight in root_edges
    )
    lower_bound = adjusted_weight - 2.0 * sum(node_penalties)
    degrees = _degrees(n, tree_edges + root_edges)

    return AdjustedOneTreeResult(
        root_city=root_city,
        adjusted_weight=adjusted_weight,
        lower_bound=lower_bound,
        degrees=degrees,
        tree_edges=tree_edges,
        root_edges=root_edges,
        penalties=node_penalties,
        metadata={"proof": LAGRANGIAN_ONE_TREE_PROOF},
    )


def optimize_held_karp_one_tree(
    matrix: Matrix,
    *,
    root_city: City = 0,
    iterations: int = 100,
    initial_step_size: float = 100.0,
    step_decay: float = 0.95,
) -> HeldKarpOneTreeResult:
    """Run deterministic subgradient updates and keep the best Lagrangian 1-tree bound."""

    validate_matrix(matrix)
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if initial_step_size <= 0:
        raise ValueError("initial_step_size must be positive")
    if not 0 < step_decay <= 1:
        raise ValueError("step_decay must be in (0, 1]")

    n = len(matrix)
    _validate_root_city(n, root_city)
    penalties = [0.0] * n
    trace: list[HeldKarpIteration] = []
    best_bound: float | None = None
    best_iteration = 0
    best_penalties = list(penalties)

    for iteration in range(iterations):
        step_size = initial_step_size * (step_decay**iteration)
        one_tree = adjusted_one_tree_lower_bound(matrix, root_city=root_city, penalties=penalties)
        trace.append(
            HeldKarpIteration(
                iteration=iteration,
                step_size=step_size,
                lower_bound=one_tree.lower_bound,
                adjusted_weight=one_tree.adjusted_weight,
                degrees=one_tree.degrees,
                penalties=list(penalties),
            )
        )
        if best_bound is None or one_tree.lower_bound > best_bound:
            best_bound = one_tree.lower_bound
            best_iteration = iteration
            best_penalties = list(penalties)
        if all(degree == 2 for degree in one_tree.degrees):
            break
        penalties = subgradient_update(
            penalties=penalties,
            degrees=one_tree.degrees,
            step_size=step_size,
        )

    assert best_bound is not None
    return HeldKarpOneTreeResult(
        algorithm=HELD_KARP_ONE_TREE_ALGORITHM,
        root_city=root_city,
        best_lower_bound=best_bound,
        best_iteration=best_iteration,
        iteration_count=len(trace),
        iterations=trace,
        best_penalties=best_penalties,
        metadata={"proof": HELD_KARP_ONE_TREE_PROOF},
    )


def subgradient_update(
    *,
    penalties: list[float],
    degrees: list[int],
    step_size: float,
) -> list[float]:
    if len(penalties) != len(degrees):
        raise ValueError("penalties and degrees must have the same length")
    return [penalty + step_size * (degree - 2) for penalty, degree in zip(penalties, degrees)]


def held_karp_one_tree_payload(
    result: HeldKarpOneTreeResult,
    *,
    input_file: Path,
    n: int,
    upper_bound: int | float,
    upper_bound_artifact: Path,
    previous_lower_bound_artifact: Path,
    proof_note: Path,
    command: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    absolute_gap = upper_bound - result.best_lower_bound
    return {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "n": n,
        "root_city": result.root_city,
        "lower_bound": result.best_lower_bound,
        "upper_bound": upper_bound,
        "absolute_gap": absolute_gap,
        "relative_gap": absolute_gap / upper_bound,
        "best_iteration": result.best_iteration,
        "iteration_count": result.iteration_count,
        "parameters": parameters,
        "best_penalties": result.best_penalties,
        "iterations": [_compact_iteration_payload(iteration) for iteration in result.iterations],
        "upper_bound_artifact": str(upper_bound_artifact),
        "previous_lower_bound_artifact": str(previous_lower_bound_artifact),
        "proof_note": str(proof_note),
        "metadata": result.metadata,
        "command": command,
        "created_at": datetime.now(UTC).isoformat(),
    }


def save_held_karp_one_tree_result(
    result: HeldKarpOneTreeResult,
    *,
    output_path: Path,
    input_file: Path,
    n: int,
    upper_bound: int | float,
    upper_bound_artifact: Path,
    previous_lower_bound_artifact: Path,
    proof_note: Path,
    command: str,
    parameters: dict[str, Any],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = held_karp_one_tree_payload(
        result,
        input_file=input_file,
        n=n,
        upper_bound=upper_bound,
        upper_bound_artifact=upper_bound_artifact,
        previous_lower_bound_artifact=previous_lower_bound_artifact,
        proof_note=proof_note,
        command=command,
        parameters=parameters,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _compact_iteration_payload(iteration: HeldKarpIteration) -> dict[str, float | int]:
    degree_deviations = [degree - 2 for degree in iteration.degrees]
    return {
        "iteration": iteration.iteration,
        "step_size": iteration.step_size,
        "lower_bound": iteration.lower_bound,
        "adjusted_weight": iteration.adjusted_weight,
        "degree_violation_l1": sum(abs(value) for value in degree_deviations),
        "degree_violation_linf": max(abs(value) for value in degree_deviations),
    }


def _adjusted_mst_edges(
    matrix: Matrix,
    *,
    root_city: City,
    penalties: list[float],
) -> list[tuple[City, City, float]]:
    vertices = [city for city in range(len(matrix)) if city != root_city]
    if len(vertices) < 2:
        return []

    start = vertices[0]
    included = {start}
    edges: list[tuple[City, City, float]] = []
    best_crossing_edge: dict[City, tuple[City, City, float]] = {
        city: (start, city, _adjusted_cost(matrix, start, city, penalties))
        for city in vertices
        if city != start
    }

    while len(included) < len(vertices):
        next_edge = min(
            (edge for city, edge in best_crossing_edge.items() if city not in included),
            key=_edge_sort_key,
        )
        from_city, to_city, _weight = next_edge
        included.add(to_city)
        edges.append(next_edge)

        for city in vertices:
            if city in included:
                continue
            candidate = (to_city, city, _adjusted_cost(matrix, to_city, city, penalties))
            if _edge_sort_key(candidate) < _edge_sort_key(best_crossing_edge[city]):
                best_crossing_edge[city] = candidate

    return edges


def _two_cheapest_adjusted_root_edges(
    matrix: Matrix,
    *,
    root_city: City,
    penalties: list[float],
) -> list[tuple[City, City, float]]:
    candidates = [
        (root_city, city, _adjusted_cost(matrix, root_city, city, penalties))
        for city in range(len(matrix))
        if city != root_city
    ]
    if len(candidates) < 2:
        raise ValueError("1-tree lower bound requires at least three cities")
    return sorted(candidates, key=_edge_sort_key)[:2]


def _adjusted_cost(matrix: Matrix, from_city: City, to_city: City, penalties: list[float]) -> float:
    return float(matrix[from_city][to_city]) + penalties[from_city] + penalties[to_city]


def _degrees(n: int, edges: list[tuple[City, City, float]]) -> list[int]:
    degrees = [0] * n
    for from_city, to_city, _weight in edges:
        degrees[from_city] += 1
        degrees[to_city] += 1
    return degrees


def _validate_root_city(n: int, root_city: City) -> None:
    if root_city < 0 or root_city >= n:
        raise ValueError(f"root city out of range: {root_city}, expected 0..{n - 1}")


def _edge_sort_key(edge: tuple[City, City, float]) -> tuple[float, City, City]:
    from_city, to_city, weight = edge
    return weight, from_city, to_city
