#!/usr/bin/env python3
"""Step 11: run LKH over multiple seeds and keep only verified best artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
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

ALGORITHM = "lkh_2_0_11_multiseed"
CURRENT_UPPER_BOUND = 73934
LOWER_BOUND_ARTIFACT = Path("results/best/step9-held-karp-one-tree.json")
BEST_OUTPUT_PATH = Path("results/best/step11-lkh-multiseed-best.json")
RUN_OUTPUT_PATH = Path("results/runs/step11-lkh-multiseed.json")
LKH_BINARY = Path("tools/LKH-2.0.11/LKH")
TSPLIB_PATH = Path("data/processed/challenge-full-matrix.tsp")
TSPLIB_NAME = "tsp_1114_challenge"
TRACE_LEVEL = 1


def parse_seed_spec(seed_spec: str) -> list[int]:
    seeds: list[int] = []
    for part in seed_spec.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if end < start:
                raise ValueError(f"invalid descending seed range: {token}")
            seeds.extend(range(start, end + 1))
        else:
            seeds.append(int(token))
    if not seeds:
        raise ValueError("at least one seed is required")
    return seeds


def choose_best_run(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        raise ValueError("cannot choose best run from an empty run list")
    return min(runs, key=lambda run: run["verified_length"])


def output_path_for_best_length(best_verified_length: int) -> Path:
    if best_verified_length < CURRENT_UPPER_BOUND:
        return BEST_OUTPUT_PATH
    return RUN_OUTPUT_PATH


def step11_payload(
    *,
    runs: list[dict[str, Any]],
    seed_spec: str,
    runs_per_seed: int,
    max_trials: int | None,
    lower_bound: float,
    command: str,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    failures = failures or []
    best = choose_best_run(runs)
    best_length = int(best["verified_length"])
    absolute_gap = best_length - lower_bound
    improved = best_length < CURRENT_UPPER_BOUND
    return {
        "algorithm": ALGORITHM,
        "input_file": str(CHALLENGE_MATRIX_PATH),
        "tsplib_file": str(TSPLIB_PATH),
        "n": 1114,
        "seed_spec": seed_spec,
        "runs_per_seed": runs_per_seed,
        "max_trials": max_trials,
        "current_upper_bound": CURRENT_UPPER_BOUND,
        "best_verified_length": best_length,
        "best_seed": best["seed"],
        "best_run": best,
        "improved_current_upper_bound": improved,
        "improvement": CURRENT_UPPER_BOUND - best_length,
        "lower_bound": lower_bound,
        "absolute_gap": absolute_gap,
        "relative_gap": absolute_gap / best_length,
        "runs_completed": len(runs),
        "runs_failed": len(failures),
        "failures": failures,
        "runs": runs,
        "output_policy": str(output_path_for_best_length(best_length)),
        "command": command,
        "lkh_binary": str(LKH_BINARY),
        "created_at": datetime.now(UTC).isoformat(),
    }


def run_lkh_seed(*, seed: int, runs_per_seed: int, max_trials: int | None, matrix: list[list[int]]) -> dict[str, Any]:
    parameter_path = Path(f"data/processed/lkh-step11-seed-{seed}.par")
    output_tour_path = Path(f"data/processed/lkh-step11-seed-{seed}.tour")
    write_step11_parameter_file(
        parameter_path=ROOT / parameter_path,
        problem_file=TSPLIB_PATH,
        output_tour_file=output_tour_path,
        seed=seed,
        runs_per_seed=runs_per_seed,
        max_trials=max_trials,
    )

    command = [str(ROOT / LKH_BINARY), str(ROOT / parameter_path)]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    runtime_seconds = time.perf_counter() - started

    tour = parse_tsplib_tour(ROOT / output_tour_path)
    validate_tour(tour, len(matrix))
    verified_length = tour_length(matrix, tour, validate=True)
    solver_length = parse_solver_length(ROOT / output_tour_path) or verified_length
    if solver_length != verified_length:
        raise AssertionError(
            f"solver/project length mismatch for seed {seed}: {solver_length} != {verified_length}"
        )

    return {
        "seed": seed,
        "solver_length": solver_length,
        "verified_length": verified_length,
        "runtime_seconds": round(runtime_seconds, 6),
        "parameter_file": str(parameter_path),
        "output_tour_file": str(output_tour_path),
        "command": " ".join(command),
        "parameters": {
            "runs": runs_per_seed,
            "seed": seed,
            "trace_level": TRACE_LEVEL,
            "max_trials": max_trials,
        },
        "lkh_stdout_tail": "\n".join(completed.stdout.strip().splitlines()[-12:]),
    }


def write_step11_parameter_file(
    *,
    parameter_path: Path,
    problem_file: Path,
    output_tour_file: Path,
    seed: int,
    runs_per_seed: int,
    max_trials: int | None,
) -> None:
    lines = [
        f"PROBLEM_FILE = {problem_file}",
        f"OUTPUT_TOUR_FILE = {output_tour_file}",
        f"RUNS = {runs_per_seed}",
    ]
    if max_trials is not None:
        lines.append(f"MAX_TRIALS = {max_trials}")
    lines.extend([f"SEED = {seed}", f"TRACE_LEVEL = {TRACE_LEVEL}", ""])
    parameter_path.parent.mkdir(parents=True, exist_ok=True)
    parameter_path.write_text("\n".join(lines), encoding="utf-8")


def parse_solver_length(tour_file: Path) -> int | None:
    for line in tour_file.read_text(encoding="utf-8").splitlines():
        match = re.search(r"Length\s*=\s*(\d+)", line)
        if match:
            return int(match.group(1))
    return None


def load_lower_bound() -> float:
    return float(json.loads((ROOT / LOWER_BOUND_ARTIFACT).read_text(encoding="utf-8"))["lower_bound"])


def save_payload(payload: dict[str, Any]) -> Path:
    output_path = Path(payload["output_policy"])
    (ROOT / output_path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", required=True, help="Seed list/range, e.g. 1-20 or 1,3,7")
    parser.add_argument("--runs", type=int, default=1, help="LKH RUNS value per seed")
    parser.add_argument("--max-trials", type=int, default=None, help="Optional LKH MAX_TRIALS value")
    args = parser.parse_args(argv)

    if not (ROOT / LKH_BINARY).exists():
        raise FileNotFoundError(f"LKH binary not found: {LKH_BINARY}")
    seeds = parse_seed_spec(args.seeds)
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    write_explicit_tsplib(data.matrix, ROOT / TSPLIB_PATH, name=TSPLIB_NAME)

    completed_runs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for seed in seeds:
        try:
            run = run_lkh_seed(seed=seed, runs_per_seed=args.runs, max_trials=args.max_trials, matrix=data.matrix)
            completed_runs.append(run)
            print(f"seed={seed} verified_length={run['verified_length']} runtime={run['runtime_seconds']:.3f}s")
        except Exception as exc:  # preserve failures without hiding successful runs
            failures.append({"seed": seed, "error": repr(exc)})
            print(f"seed={seed} failed={exc!r}")

    if not completed_runs:
        raise RuntimeError("all LKH seed runs failed")

    command = "python experiments/step11_lkh_multiseed.py " + " ".join(sys.argv[1:])
    payload = step11_payload(
        runs=completed_runs,
        seed_spec=args.seeds,
        runs_per_seed=args.runs,
        max_trials=args.max_trials,
        lower_bound=load_lower_bound(),
        command=command,
        failures=failures,
    )
    output_path = save_payload(payload)

    print(f"algorithm={payload['algorithm']}")
    print(f"seeds_completed={payload['runs_completed']}")
    print(f"seeds_failed={payload['runs_failed']}")
    print(f"best_seed={payload['best_seed']}")
    print(f"best_verified_length={payload['best_verified_length']}")
    print(f"improved_current_upper_bound={payload['improved_current_upper_bound']}")
    print(f"output={output_path}")


if __name__ == "__main__":
    main()
