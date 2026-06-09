#!/usr/bin/env python3
"""Step 6: run LKH on the exported challenge matrix and verify the tour."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io.matrix_loader import load_matrix
from src.io.tsplib import parse_tsplib_tour, write_explicit_tsplib
from src.io.validation import validate_tour
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

LKH_BINARY = Path("tools/LKH-2.0.11/LKH")
TSPLIB_PATH = Path("data/processed/challenge-full-matrix.tsp")
PARAMETER_PATH = Path("data/processed/lkh-step6.par")
LKH_TOUR_PATH = Path("data/processed/lkh-step6-output.tour")
OUTPUT_PATH = Path("results/best/step6-lkh-best.json")
PREVIOUS_UPPER_ARTIFACT = Path("results/best/step4-two-opt-best.json")
COMMAND = "python experiments/step6_lkh_benchmark.py"
TSPLIB_NAME = "tsp_1114_challenge"
SEED = 1
RUNS = 1
TRACE_LEVEL = 1


def main() -> None:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    previous_upper = _load_previous_upper_bound(ROOT / PREVIOUS_UPPER_ARTIFACT)
    _ensure_lkh_binary(ROOT / LKH_BINARY)
    write_explicit_tsplib(data.matrix, ROOT / TSPLIB_PATH, name=TSPLIB_NAME)
    _write_parameter_file(ROOT / PARAMETER_PATH)

    completed = subprocess.run(
        [str(ROOT / LKH_BINARY), str(ROOT / PARAMETER_PATH)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )

    tour = parse_tsplib_tour(ROOT / LKH_TOUR_PATH)
    validate_tour(tour, data.n)
    length = tour_length(data.matrix, tour, validate=True)
    if length >= previous_upper:
        raise AssertionError(f"LKH did not improve upper bound: {length} >= {previous_upper}")

    payload = _payload(
        n=data.n,
        length=length,
        tour=tour,
        previous_upper=previous_upper,
        lkh_output=completed.stdout,
    )
    (ROOT / OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / OUTPUT_PATH).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"algorithm={payload['algorithm']}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"previous_upper_bound={previous_upper}")
    print(f"best_length={length}")
    print(f"improvement={previous_upper - length}")
    print(f"seed={SEED}")
    print(f"runs={RUNS}")
    print(f"output={OUTPUT_PATH}")


def _write_parameter_file(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                f"PROBLEM_FILE = {TSPLIB_PATH}",
                f"OUTPUT_TOUR_FILE = {LKH_TOUR_PATH}",
                f"RUNS = {RUNS}",
                f"SEED = {SEED}",
                f"TRACE_LEVEL = {TRACE_LEVEL}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _payload(*, n: int, length: int, tour: list[int], previous_upper: int, lkh_output: str) -> dict[str, Any]:
    return {
        "algorithm": "lkh_2_0_11",
        "input_file": str(CHALLENGE_MATRIX_PATH),
        "tsplib_file": str(TSPLIB_PATH),
        "n": n,
        "length": length,
        "tour": tour,
        "previous_upper_bound": previous_upper,
        "improvement": previous_upper - length,
        "seed": SEED,
        "runs": RUNS,
        "lkh_binary": str(LKH_BINARY),
        "lkh_tour_file": str(LKH_TOUR_PATH),
        "command": COMMAND,
        "created_at": datetime.now(UTC).isoformat(),
        "lkh_stdout_tail": "\n".join(lkh_output.strip().splitlines()[-20:]),
    }


def _load_previous_upper_bound(path: Path) -> int:
    return int(json.loads(path.read_text(encoding="utf-8"))["length"])


def _ensure_lkh_binary(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"LKH binary not found: {path}. Build it under tools/LKH-2.0.11/LKH first."
        )


if __name__ == "__main__":
    main()
