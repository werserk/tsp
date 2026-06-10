#!/usr/bin/env python3
"""Step 14: Concorde no-branch/cutting-plane lower-bound extraction."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integrations.concorde import parse_concorde_log, verify_tsplib_full_matrix_mapping
from src.io.matrix_loader import load_matrix
from src.io.tsplib import parse_tsplib_tour, write_explicit_tsplib
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

CURRENT_LOWER_BOUND = 72711.81768955325
CURRENT_UPPER_BOUND = 73934
TSPLIB_PATH = Path("data/processed/M-full-matrix.tsp")
LOG_PATH = Path("results/runs/step14-concorde-root.log")
X_PATH = Path("results/runs/step14-concorde-root.x")
TOUR_PATH = Path("results/runs/step14-concorde-tour.out")
RUN_ARTIFACT_PATH = Path("results/runs/step14-concorde-no-branch-run.json")
BEST_ARTIFACT_PATH = Path("results/best/step14-concorde-no-branch-lower-bound.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--concorde", required=True, type=Path, help="Path to Concorde binary")
    parser.add_argument("--seed", type=int, default=None, help="Optional Concorde random seed")
    parser.add_argument("--export-only", action="store_true", help="Only export and verify TSPLIB input")
    return parser.parse_args()


def command_for(concorde: Path, *, seed: int | None) -> list[str]:
    command = [
        str(concorde),
        "-B",
    ]
    if seed is not None:
        command.extend(["-s", str(seed)])
    command.extend([
        "-u",
        str(CURRENT_UPPER_BOUND),
        "-n",
        "results/runs/step14-concorde-root-problem",
        "-X",
        str(X_PATH),
        "-o",
        str(TOUR_PATH),
        str(TSPLIB_PATH),
    ])
    return command


def verify_concorde_tour_if_present(matrix: list[list[int]], tour_path: Path) -> dict[str, Any] | None:
    if not tour_path.exists() or tour_path.stat().st_size == 0:
        return None
    try:
        tour = parse_tsplib_tour(tour_path)
    except Exception as exc:
        return {
            "tour_file": str(tour_path),
            "verified": False,
            "error": f"could not parse TSPLIB TOUR_SECTION: {exc}",
        }
    length = tour_length(matrix, tour, validate=True)
    return {
        "tour_file": str(tour_path),
        "verified": True,
        "length": length,
        "city_count": len(tour),
        "verification": "parse_tsplib_tour + tour_length(matrix, tour, validate=True)",
    }


def build_payload(*, concorde: Path, command: list[str], runtime_seconds: float | None) -> dict[str, Any]:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    mapping = verify_tsplib_full_matrix_mapping(data.matrix, ROOT / TSPLIB_PATH)
    summary = parse_concorde_log(ROOT / LOG_PATH)
    review = summary.review_decision(CURRENT_LOWER_BOUND, CURRENT_UPPER_BOUND)
    tour_verification = verify_concorde_tour_if_present(data.matrix, ROOT / TOUR_PATH)
    lower_bound = float(review["lower_bound_candidate"])
    absolute_gap = CURRENT_UPPER_BOUND - lower_bound
    return {
        "type": "lower_bound",
        "algorithm": "concorde_no_branch_cutting_plane",
        "method": "Concorde -B no-branch root/cutting-plane lower-bound extraction",
        "input_matrix": str(CHALLENGE_MATRIX_PATH),
        "tsplib_input": str(TSPLIB_PATH),
        "n": data.n,
        "lower_bound": lower_bound,
        "previous_lower_bound": CURRENT_LOWER_BOUND,
        "upper_bound": CURRENT_UPPER_BOUND,
        "absolute_gap": absolute_gap,
        "relative_gap_to_lower": absolute_gap / lower_bound,
        "relative_gap_to_upper": absolute_gap / CURRENT_UPPER_BOUND,
        "integer_lower_bound": int(lower_bound) + (0 if lower_bound.is_integer() else 1),
        "concorde_binary": str(concorde),
        "command": " ".join(command),
        "log_path": str(LOG_PATH),
        "generated_files": {
            "fractional_solution": str(X_PATH) if (ROOT / X_PATH).exists() else None,
            "tour_output": str(TOUR_PATH) if (ROOT / TOUR_PATH).exists() else None,
        },
        "runtime_seconds": runtime_seconds,
        "concorde_log_summary": summary.to_dict(),
        "mapping_verification": mapping,
        "tour_verification": tour_verification,
        "review_gate": review,
        "proof_sketch": "Concorde -B stops after root/cutting-plane processing without branching. The reported LP lower bound is a relaxation/cutting-plane lower bound for the symmetric TSP instance, so it is <= OPT if the TSPLIB mapping is correct. The log is preserved and parsed separately from tour/upper-bound fields.",
        "created_at": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    args = parse_args()
    concorde = args.concorde
    if not concorde.exists():
        raise SystemExit(f"Concorde binary not found: {concorde}")

    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    write_explicit_tsplib(data.matrix, ROOT / TSPLIB_PATH, name="hse1114")
    mapping = verify_tsplib_full_matrix_mapping(data.matrix, ROOT / TSPLIB_PATH)
    print(f"exported={TSPLIB_PATH}")
    print(f"mapping={mapping}")
    if args.export_only:
        return

    (ROOT / LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    command = command_for(concorde, seed=args.seed)
    started = perf_counter()
    with (ROOT / LOG_PATH).open("w", encoding="utf-8") as log_file:
        process = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        log_file.write(process.stdout)
    runtime_seconds = perf_counter() - started
    print(process.stdout, end="")
    print(f"return_code={process.returncode}")
    print(f"runtime_seconds={runtime_seconds:.3f}")
    if process.returncode != 0:
        raise SystemExit(f"Concorde failed with return code {process.returncode}; log={LOG_PATH}")

    payload = build_payload(concorde=concorde, command=command, runtime_seconds=runtime_seconds)
    output_path = BEST_ARTIFACT_PATH if payload["review_gate"]["decision"] == "promote" else RUN_ARTIFACT_PATH
    (ROOT / output_path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"parsed_lower_bound={payload['lower_bound']}")
    print(f"review_decision={payload['review_gate']['decision']}")
    print(f"artifact={output_path}")


if __name__ == "__main__":
    main()
