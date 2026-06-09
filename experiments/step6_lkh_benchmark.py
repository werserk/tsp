#!/usr/bin/env python3
"""Step 6: run LKH on the challenge instance and verify the returned tour."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integrations.lkh import (
    LKH_ALGORITHM,
    LKHResult,
    export_tsplib_full_matrix,
    parse_lkh_tour,
    save_lkh_result,
    write_lkh_parameter_file,
)
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

TSPLIB_PATH = Path("data/processed/lkh/challenge-1114-full-matrix.tsp")
PARAMETER_PATH = Path("data/processed/lkh/challenge-1114.par")
LKH_TOUR_PATH = Path("data/processed/lkh/challenge-1114.lkh.tour")
OUTPUT_PATH = Path("results/best/step6-lkh-best.json")
PREVIOUS_UPPER_ARTIFACT = Path("results/best/step4-two-opt-best.json")
LOWER_BOUND_ARTIFACT = Path("results/best/step5-lower-bound-baseline.json")
COMMAND = "python experiments/step6_lkh_benchmark.py"
RUNS = 10
MAX_TRIALS = 10000
SEED = 7
LKH_TIMEOUT_SECONDS = 540


def main() -> None:
    lkh_binary = _find_lkh_binary()
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    previous_upper_bound = _read_int_field(ROOT / PREVIOUS_UPPER_ARTIFACT, "length")
    lower_bound = _read_int_field(ROOT / LOWER_BOUND_ARTIFACT, "lower_bound")

    tsplib_path = ROOT / TSPLIB_PATH
    parameter_path = ROOT / PARAMETER_PATH
    lkh_tour_path = ROOT / LKH_TOUR_PATH

    export_tsplib_full_matrix(
        data.matrix,
        output_path=tsplib_path,
        name="challenge_1114_full_matrix",
    )
    write_lkh_parameter_file(
        parameter_path=parameter_path,
        problem_file=TSPLIB_PATH,
        output_tour_file=LKH_TOUR_PATH,
        runs=RUNS,
        max_trials=MAX_TRIALS,
        seed=SEED,
    )

    log_path = ROOT / "results/runs/step6-lkh-run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    try:
        completed = subprocess.run(
            [str(lkh_binary), str(parameter_path)],
            check=True,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=LKH_TIMEOUT_SECONDS,
        )
        log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "ignore")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "ignore")
        log_path.write_text(stdout + stderr + "\n[LKH timed out; parsing best tour file if present]\n", encoding="utf-8")
        if not lkh_tour_path.exists():
            raise

    tour = parse_lkh_tour(lkh_tour_path)
    length = tour_length(data.matrix, tour, validate=True)
    result = LKHResult(
        algorithm=LKH_ALGORITHM,
        tour=tour,
        length=length,
        metadata={
            "runs": RUNS,
            "max_trials": MAX_TRIALS,
            "seed": SEED,
            "timeout_seconds": LKH_TIMEOUT_SECONDS,
            "timed_out": timed_out,
            "parameter_file": str(PARAMETER_PATH),
            "tsplib_file": str(TSPLIB_PATH),
            "lkh_tour_file": str(LKH_TOUR_PATH),
            "log_file": "results/runs/step6-lkh-run.log",
        },
    )
    save_lkh_result(
        result,
        output_path=ROOT / OUTPUT_PATH,
        input_file=CHALLENGE_MATRIX_PATH,
        n=data.n,
        previous_upper_bound=previous_upper_bound,
        lower_bound=lower_bound,
        command=COMMAND,
        lkh_binary=lkh_binary,
    )

    print(f"algorithm={result.algorithm}")
    print(f"n={data.n}")
    print(f"length={result.length}")
    print(f"previous_upper_bound={previous_upper_bound}")
    print(f"improvement_vs_previous_upper={previous_upper_bound - result.length}")
    print(f"timed_out={timed_out}")
    print(f"lower_bound={lower_bound}")
    print(f"absolute_gap={result.length - lower_bound}")
    print(f"relative_gap={(result.length - lower_bound) / result.length:.6f}")
    print(f"output={OUTPUT_PATH}")


def _find_lkh_binary() -> Path:
    for candidate in [ROOT / "tools/LKH-2.0.11/LKH", ROOT / "tools/LKH/LKH", Path("LKH")]:
        if candidate.is_file():
            return candidate
    found = shutil.which("LKH") or shutil.which("lkh")
    if found:
        return Path(found)
    raise FileNotFoundError("LKH binary not found; expected tools/LKH-2.0.11/LKH or LKH in PATH")


def _read_int_field(path: Path, field: str) -> int:
    return int(json.loads(path.read_text(encoding="utf-8"))[field])


if __name__ == "__main__":
    main()
