from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.bounds.mst import minimum_spanning_tree
from src.io.validation import validate_matrix
from src.tsp.types import City, Matrix

ONE_TREE_LOWER_BOUND_ALGORITHM = "one_tree_lower_bound"
SEVERAL_ROOT_ONE_TREE_ALGORITHM = "several_root_one_tree_lower_bound"
ONE_TREE_PROOF = "mst_without_root_plus_two_cheapest_root_edges"
SEVERAL_ROOT_ONE_TREE_PROOF = "max_of_valid_fixed_root_one_tree_lower_bounds"


@dataclass(frozen=True)
class OneTreeResult:
    algorithm: str
    root_city: City
    mst_without_root_weight: int
    root_edges: list[tuple[City, City, int]]
    lower_bound: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class SeveralRootOneTreeResult:
    algorithm: str
    candidate_roots: list[City]
    best_root_city: City
    lower_bound: int
    evaluated_bounds: list[dict[str, int]]
    metadata: dict[str, Any]


def one_tree_lower_bound(matrix: Matrix, *, root_city: City = 0) -> OneTreeResult:
    """Return the simple 1-tree lower bound for a fixed root city."""

    validate_matrix(matrix)
    _validate_root_city(matrix, root_city)

    mst = minimum_spanning_tree(matrix, excluded_vertex=root_city)
    root_edges = two_cheapest_incident_edges(matrix, root_city=root_city)
    lower_bound = mst.weight + sum(weight for _, _, weight in root_edges)

    return OneTreeResult(
        algorithm=ONE_TREE_LOWER_BOUND_ALGORITHM,
        root_city=root_city,
        mst_without_root_weight=mst.weight,
        root_edges=root_edges,
        lower_bound=lower_bound,
        metadata={"proof": ONE_TREE_PROOF},
    )


def best_one_tree_lower_bound(
    matrix: Matrix,
    *,
    candidate_roots: list[City] | None = None,
) -> SeveralRootOneTreeResult:
    """Return the strongest fixed-root 1-tree bound among candidate roots."""

    validate_matrix(matrix)
    roots = list(range(len(matrix))) if candidate_roots is None else list(candidate_roots)
    if not roots:
        raise ValueError("at least one candidate root is required")

    evaluated_bounds: list[dict[str, int]] = []
    best_result: OneTreeResult | None = None
    for root_city in roots:
        result = one_tree_lower_bound(matrix, root_city=root_city)
        evaluated_bounds.append({"root_city": root_city, "lower_bound": result.lower_bound})
        if best_result is None or (result.lower_bound, -result.root_city) > (
            best_result.lower_bound,
            -best_result.root_city,
        ):
            best_result = result

    assert best_result is not None
    return SeveralRootOneTreeResult(
        algorithm=SEVERAL_ROOT_ONE_TREE_ALGORITHM,
        candidate_roots=roots,
        best_root_city=best_result.root_city,
        lower_bound=best_result.lower_bound,
        evaluated_bounds=evaluated_bounds,
        metadata={"proof": SEVERAL_ROOT_ONE_TREE_PROOF},
    )


def two_cheapest_incident_edges(matrix: Matrix, *, root_city: City) -> list[tuple[City, City, int]]:
    """Return two cheapest edges incident to root, tie-broken by city index."""

    validate_matrix(matrix)
    _validate_root_city(matrix, root_city)
    candidates = [
        (root_city, city, matrix[root_city][city])
        for city in range(len(matrix))
        if city != root_city
    ]
    if len(candidates) < 2:
        raise ValueError("1-tree lower bound requires at least three cities")
    return sorted(candidates, key=_edge_sort_key)[:2]


def one_tree_payload(
    result: OneTreeResult,
    *,
    input_file: Path,
    n: int,
    upper_bound: int,
    upper_bound_artifact: Path,
    proof_note: Path,
    command: str,
) -> dict[str, Any]:
    absolute_gap = upper_bound - result.lower_bound
    return {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "n": n,
        "root_city": result.root_city,
        "mst_without_root_weight": result.mst_without_root_weight,
        "two_cheapest_root_edges": result.root_edges,
        "lower_bound": result.lower_bound,
        "upper_bound": upper_bound,
        "absolute_gap": absolute_gap,
        "relative_gap": absolute_gap / upper_bound,
        "upper_bound_artifact": str(upper_bound_artifact),
        "proof_note": str(proof_note),
        "metadata": result.metadata,
        "command": command,
        "created_at": datetime.now(UTC).isoformat(),
    }


def several_root_one_tree_payload(
    result: SeveralRootOneTreeResult,
    *,
    input_file: Path,
    n: int,
    upper_bound: int,
    upper_bound_artifact: Path,
    proof_note: Path,
    command: str,
) -> dict[str, Any]:
    absolute_gap = upper_bound - result.lower_bound
    return {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "n": n,
        "candidate_count": len(result.candidate_roots),
        "candidate_roots": result.candidate_roots,
        "best_root_city": result.best_root_city,
        "lower_bound": result.lower_bound,
        "upper_bound": upper_bound,
        "absolute_gap": absolute_gap,
        "relative_gap": absolute_gap / upper_bound,
        "upper_bound_artifact": str(upper_bound_artifact),
        "proof_note": str(proof_note),
        "evaluated_bounds": result.evaluated_bounds,
        "metadata": result.metadata,
        "command": command,
        "created_at": datetime.now(UTC).isoformat(),
    }


def save_several_root_one_tree_result(
    result: SeveralRootOneTreeResult,
    *,
    output_path: Path,
    input_file: Path,
    n: int,
    upper_bound: int,
    upper_bound_artifact: Path,
    proof_note: Path,
    command: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = several_root_one_tree_payload(
        result,
        input_file=input_file,
        n=n,
        upper_bound=upper_bound,
        upper_bound_artifact=upper_bound_artifact,
        proof_note=proof_note,
        command=command,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_one_tree_result(
    result: OneTreeResult,
    *,
    output_path: Path,
    input_file: Path,
    n: int,
    upper_bound: int,
    upper_bound_artifact: Path,
    proof_note: Path,
    command: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = one_tree_payload(
        result,
        input_file=input_file,
        n=n,
        upper_bound=upper_bound,
        upper_bound_artifact=upper_bound_artifact,
        proof_note=proof_note,
        command=command,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validate_root_city(matrix: Matrix, root_city: City) -> None:
    if root_city < 0 or root_city >= len(matrix):
        raise ValueError(f"root city out of range: {root_city}, expected 0..{len(matrix) - 1}")


def _edge_sort_key(edge: tuple[City, City, int]) -> tuple[int, City, City]:
    from_city, to_city, weight = edge
    return weight, from_city, to_city
