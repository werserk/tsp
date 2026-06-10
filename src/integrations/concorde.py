from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.tsp.types import Matrix

FINAL_BOUND_RE = re.compile(
    r"Final\s+lower\s+bound\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?),\s+upper\s+bound\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
)
EXACT_LOWER_RE = re.compile(
    r"Exact\s+lower\s+bound:\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
)
FINAL_LP_RE = re.compile(
    r"Final\s+LP\s+has\s+(\d+)\s+rows,\s+(\d+)\s+columns,\s+(\d+)\s+nonzeros"
)
OPTIMAL_RE = re.compile(
    r"Optimal\s+Solution:\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
)
BBNODES_RE = re.compile(r"Number\s+of\s+bbnodes:\s+(\d+)")


@dataclass(frozen=True)
class ConcordeLogSummary:
    final_lower_bound: float | None
    final_upper_bound: float | None
    exact_lower_bound: float | None
    lp_rows: int | None
    lp_columns: int | None
    lp_nonzeros: int | None
    optimal_solution: float | None
    branch_and_bound_nodes: int | None

    def lower_bound_candidate(self) -> float:
        return choose_concorde_lower_bound(self)

    def review_decision(self, current_lower_bound: float, current_upper_bound: float) -> dict[str, Any]:
        lower_bound = self.lower_bound_candidate()
        if lower_bound > current_upper_bound:
            decision = "reject_invalid_above_upper_bound"
        elif lower_bound > current_lower_bound:
            decision = "promote"
        else:
            decision = "reject_no_improvement"
        return {
            "decision": decision,
            "lower_bound_candidate": lower_bound,
            "current_lower_bound": current_lower_bound,
            "current_upper_bound": current_upper_bound,
            "strict_improvement": lower_bound > current_lower_bound,
            "lower_bound_le_upper_bound": lower_bound <= current_upper_bound,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_lower_bound": self.final_lower_bound,
            "final_upper_bound": self.final_upper_bound,
            "exact_lower_bound": self.exact_lower_bound,
            "lp_rows": self.lp_rows,
            "lp_columns": self.lp_columns,
            "lp_nonzeros": self.lp_nonzeros,
            "optimal_solution": self.optimal_solution,
            "branch_and_bound_nodes": self.branch_and_bound_nodes,
        }


def parse_concorde_log(log_path: Path) -> ConcordeLogSummary:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    final_lower_bound = None
    final_upper_bound = None
    for match in FINAL_BOUND_RE.finditer(text):
        final_lower_bound = float(match.group(1))
        final_upper_bound = float(match.group(2))

    exact_lower_bound = None
    for match in EXACT_LOWER_RE.finditer(text):
        exact_lower_bound = float(match.group(1))

    lp_rows = lp_columns = lp_nonzeros = None
    for match in FINAL_LP_RE.finditer(text):
        lp_rows = int(match.group(1))
        lp_columns = int(match.group(2))
        lp_nonzeros = int(match.group(3))

    optimal_solution = None
    for match in OPTIMAL_RE.finditer(text):
        optimal_solution = float(match.group(1))

    branch_and_bound_nodes = None
    for match in BBNODES_RE.finditer(text):
        branch_and_bound_nodes = int(match.group(1))

    return ConcordeLogSummary(
        final_lower_bound=final_lower_bound,
        final_upper_bound=final_upper_bound,
        exact_lower_bound=exact_lower_bound,
        lp_rows=lp_rows,
        lp_columns=lp_columns,
        lp_nonzeros=lp_nonzeros,
        optimal_solution=optimal_solution,
        branch_and_bound_nodes=branch_and_bound_nodes,
    )


def choose_concorde_lower_bound(summary: ConcordeLogSummary) -> float:
    candidates = [
        value
        for value in (summary.final_lower_bound, summary.exact_lower_bound)
        if value is not None
    ]
    if not candidates:
        raise ValueError("no Concorde lower-bound field found in log")
    return max(candidates)


def verify_tsplib_full_matrix_mapping(matrix: Matrix, tsplib_path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in tsplib_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    headers: dict[str, str] = {}
    section_index = None
    for index, line in enumerate(lines):
        if line == "EDGE_WEIGHT_SECTION":
            section_index = index + 1
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

    if section_index is None:
        raise ValueError(f"EDGE_WEIGHT_SECTION not found in {tsplib_path}")
    if headers.get("TYPE") != "TSP":
        raise ValueError(f"TSPLIB TYPE must be TSP, got {headers.get('TYPE')!r}")
    if headers.get("EDGE_WEIGHT_TYPE") != "EXPLICIT":
        raise ValueError("TSPLIB EDGE_WEIGHT_TYPE must be EXPLICIT")
    if headers.get("EDGE_WEIGHT_FORMAT") != "FULL_MATRIX":
        raise ValueError("TSPLIB EDGE_WEIGHT_FORMAT must be FULL_MATRIX")

    dimension = int(headers.get("DIMENSION", "0"))
    if dimension != len(matrix):
        raise ValueError(f"TSPLIB dimension {dimension} != source matrix dimension {len(matrix)}")

    tokens: list[str] = []
    for line in lines[section_index:]:
        if line == "EOF":
            break
        tokens.extend(line.split())

    expected_count = dimension * dimension
    if len(tokens) != expected_count:
        raise ValueError(f"TSPLIB matrix has {len(tokens)} entries, expected {expected_count}")

    entries_checked = 0
    for i, row in enumerate(matrix):
        for j, expected in enumerate(row):
            actual = int(tokens[i * dimension + j])
            if actual != expected:
                raise ValueError(
                    f"TSPLIB distance mismatch at ({i}, {j}): {actual} != {expected}"
                )
            entries_checked += 1

    return {
        "format": "TSPLIB_EXPLICIT_FULL_MATRIX",
        "dimension": dimension,
        "entries_checked": entries_checked,
        "matches_source_matrix": True,
    }
