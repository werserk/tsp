from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.io.validation import validate_matrix, validate_tour
from src.tsp.types import Matrix, Tour

LKH_ALGORITHM = "lkh_lin_kernighan_helsgaun"


@dataclass(frozen=True)
class LKHResult:
    algorithm: str
    tour: Tour
    length: int
    metadata: dict[str, Any]


def export_tsplib_full_matrix(matrix: Matrix, *, output_path: Path, name: str) -> None:
    """Export a symmetric explicit full-matrix TSP instance in TSPLIB style."""

    validate_matrix(matrix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"NAME: {name}",
        "TYPE: TSP",
        f"DIMENSION: {len(matrix)}",
        "EDGE_WEIGHT_TYPE: EXPLICIT",
        "EDGE_WEIGHT_FORMAT: FULL_MATRIX",
        "EDGE_WEIGHT_SECTION",
    ]
    lines.extend(" ".join(str(value) for value in row) for row in matrix)
    lines.append("EOF")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_lkh_parameter_file(
    *,
    parameter_path: Path,
    problem_file: Path,
    output_tour_file: Path,
    runs: int,
    max_trials: int,
    seed: int,
    trace_level: int = 1,
) -> None:
    parameter_path.parent.mkdir(parents=True, exist_ok=True)
    parameter_path.write_text(
        f"PROBLEM_FILE = {problem_file}\n"
        f"OUTPUT_TOUR_FILE = {output_tour_file}\n"
        f"RUNS = {runs}\n"
        f"MAX_TRIALS = {max_trials}\n"
        f"SEED = {seed}\n"
        f"TRACE_LEVEL = {trace_level}\n",
        encoding="utf-8",
    )


def parse_lkh_tour(tour_file: Path) -> Tour:
    """Parse a TSPLIB/LKH TOUR_SECTION file into a zero-based tour."""

    in_tour_section = False
    one_based_tour: list[int] = []
    for raw_line in tour_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "TOUR_SECTION":
            in_tour_section = True
            continue
        if not in_tour_section:
            continue
        if line in {"-1", "EOF"}:
            break
        one_based_tour.extend(int(value) for value in line.split())

    if not one_based_tour:
        raise ValueError(f"no TOUR_SECTION entries found in {tour_file}")
    tour = [city - 1 for city in one_based_tour]
    validate_tour(tour, len(tour))
    return tour


def lkh_payload(
    result: LKHResult,
    *,
    input_file: Path,
    n: int,
    previous_upper_bound: int,
    lower_bound: int,
    command: str,
    lkh_binary: Path,
) -> dict[str, Any]:
    absolute_gap = result.length - lower_bound
    return {
        "algorithm": result.algorithm,
        "input_file": str(input_file),
        "n": n,
        "length": result.length,
        "improvement_vs_previous_upper": previous_upper_bound - result.length,
        "lower_bound": lower_bound,
        "absolute_gap": absolute_gap,
        "relative_gap": absolute_gap / result.length,
        "tour": result.tour,
        "metadata": result.metadata,
        "command": command,
        "lkh_binary": str(lkh_binary),
        "created_at": datetime.now(UTC).isoformat(),
    }


def save_lkh_result(
    result: LKHResult,
    *,
    output_path: Path,
    input_file: Path,
    n: int,
    previous_upper_bound: int,
    lower_bound: int,
    command: str,
    lkh_binary: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = lkh_payload(
        result,
        input_file=input_file,
        n=n,
        previous_upper_bound=previous_upper_bound,
        lower_bound=lower_bound,
        command=command,
        lkh_binary=lkh_binary,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
