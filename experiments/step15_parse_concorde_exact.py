#!/usr/bin/env python3
"""Parse and verify Step 15 Concorde exact-closure artifacts."""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io.matrix_loader import load_matrix
from src.tsp.tour import tour_length

LOG_PATH = Path("results/runs/step15-concorde-exact.log")
TOUR_PATH = Path("results/runs/step15-concorde-exact.tour")
SUMMARY_PATH = Path("results/runs/step15-concorde-exact-summary.json")
MATRIX_PATH = Path("data/raw/matrices/M.txt")
TSPLIB_PATH = Path("data/processed/M-full-matrix.tsp")
CURRENT_LB = 73932.094971
INCUMBENT_UB = 73934


def _floats(pattern: str, text: str) -> list[float]:
    return [float(value) for value in re.findall(pattern, text)]


def _parse_log(text: str) -> dict[str, Any]:
    final_bounds = [
        (float(lb), float(ub))
        for lb, ub in re.findall(
            r"Final lower bound\s+([0-9]+(?:\.[0-9]+)?),\s+upper bound\s+([0-9]+(?:\.[0-9]+)?)",
            text,
        )
    ]
    exact_lbs = _floats(r"Exact lower bound:\s+([0-9]+(?:\.[0-9]+)?)", text)
    branch_lbs = _floats(r"LOWER BOUND:\s+([0-9]+(?:\.[0-9]+)?)", text)
    optimal_values = _floats(r"Optimal Solution:\s+([0-9]+(?:\.[0-9]+)?)", text)
    lp_shapes = [
        {"rows": int(rows), "columns": int(cols), "nonzeros": int(nonzeros)}
        for rows, cols, nonzeros in re.findall(
            r"Final LP has\s+(\d+)\s+rows,\s+(\d+)\s+columns,\s+(\d+)\s+nonzeros",
            text,
        )
    ]
    bbnodes = [int(value) for value in re.findall(r"Number of bbnodes:\s+(\d+)", text)]
    new_upperbounds = _floats(r"New upperbound[^:]*:\s+([0-9]+(?:\.[0-9]+)?)", text)
    lower_candidates = [lb for lb, _ in final_bounds] + exact_lbs + branch_lbs
    upper_candidates = [ub for _, ub in final_bounds] + optimal_values + new_upperbounds
    return {
        "final_bounds": final_bounds,
        "exact_lower_bounds": exact_lbs,
        "branch_lower_bounds": branch_lbs,
        "optimal_solutions": optimal_values,
        "lp_shapes": lp_shapes,
        "bbnodes": bbnodes,
        "new_upperbounds": new_upperbounds,
        "best_parsed_lower_bound": max(lower_candidates) if lower_candidates else None,
        "best_parsed_upper_bound": min(upper_candidates) if upper_candidates else None,
        "explicit_optimality": bool(optimal_values),
        "line_count": len(text.splitlines()),
    }


def _parse_tour(path: Path) -> list[int] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    ints = [int(x) for x in re.findall(r"-?\d+", path.read_text(encoding="utf-8", errors="ignore"))]
    if not ints:
        return None
    if len(ints) == 1115 and ints[0] == 1114:
        ints = ints[1:]
    if len(ints) > 1114:
        ints = ints[:1114]
    return ints


def main() -> None:
    text = (ROOT / LOG_PATH).read_text(encoding="utf-8", errors="ignore") if (ROOT / LOG_PATH).exists() else ""
    parsed = _parse_log(text)
    tour = _parse_tour(ROOT / TOUR_PATH)
    tour_check: dict[str, Any] | None = None
    if tour is not None:
        matrix_data = load_matrix(ROOT / MATRIX_PATH)
        length = tour_length(matrix_data.matrix, tour, validate=True)
        tour_check = {
            "path": str(TOUR_PATH),
            "city_count": len(tour),
            "verified_length": length,
            "is_73933": length == 73933,
            "is_73934": length == 73934,
        }
    lb = parsed["best_parsed_lower_bound"]
    ub = parsed["best_parsed_upper_bound"]
    closure: dict[str, Any] = {
        "success": False,
        "case": None,
        "reason": "no closure condition met",
    }
    if tour_check and tour_check["verified_length"] == 73933:
        closure = {"success": True, "case": "A", "reason": "verified Concorde tour length 73933"}
    elif lb is not None and lb > 73933 and (ub == 73934 or ub is None):
        closure = {"success": True, "case": "B", "reason": "parsed lower bound > 73933 with incumbent UB 73934"}
    elif parsed["explicit_optimality"] and any(math.isclose(value, 73934, abs_tol=1e-9) for value in parsed["optimal_solutions"]):
        closure = {"success": True, "case": "C", "reason": "Concorde explicitly proved optimality of 73934"}

    payload = {
        "type": "exact_closure_attempt",
        "algorithm": "concorde_branch_and_cut",
        "input_matrix": str(MATRIX_PATH),
        "tsplib_input": str(TSPLIB_PATH),
        "log_path": str(LOG_PATH),
        "tour_path": str(TOUR_PATH) if (ROOT / TOUR_PATH).exists() else None,
        "current_lower_bound_before_step15": CURRENT_LB,
        "incumbent_upper_bound": INCUMBENT_UB,
        "parsed": parsed,
        "tour_verification": tour_check,
        "closure": closure,
        "created_at": datetime.now(UTC).isoformat(),
    }
    out = ROOT / SUMMARY_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
