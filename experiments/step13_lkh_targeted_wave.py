#!/usr/bin/env python3
"""Step 13: targeted LKH configs with separate artifacts from Step 12."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
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

CURRENT_UPPER_BOUND = 73934
LKH_BINARY = Path("tools/LKH-2.0.11/LKH")
TSPLIB_PATH = Path("data/processed/challenge-full-matrix.tsp")
LOWER_BOUND_ARTIFACT = Path("results/best/step9-held-karp-one-tree.json")
PROGRESS_PATH = Path("results/runs/step13-lkh-targeted-progress.jsonl")
RUN_OUTPUT_PATH = Path("results/runs/step13-lkh-targeted-wave.json")
BEST_OUTPUT_PATH = Path("results/best/step13-lkh-targeted-upper-bound.json")
TRACE_LEVEL = 1


@dataclass(frozen=True)
class Config:
    config_id: str
    parameters: tuple[tuple[str, str], ...]


def default_configs() -> list[Config]:
    return [
        Config("E_patch_r3", (("RUNS", "3"), ("PATCHING_C", "3"), ("PATCHING_A", "2"))),
        Config("F_move5_r3", (("RUNS", "3"), ("MOVE_TYPE", "5"))),
        Config("G_backtracking_r3", (("RUNS", "3"), ("BACKTRACKING", "YES"))),
        Config("H_gain_no_r3", (("RUNS", "3"), ("GAIN_CRITERION", "NO"))),
    ]


def parse_seed_spec(spec: str) -> list[int]:
    seeds: list[int] = []
    for part in spec.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(token))
    if not seeds:
        raise ValueError("empty seed spec")
    return seeds


def selected_configs(spec: str | None) -> list[Config]:
    configs = default_configs()
    if not spec:
        return configs
    by_id = {c.config_id: c for c in configs}
    return [by_id[token.strip()] for token in spec.split(",") if token.strip()]


def load_lower_bound() -> float:
    return float(json.loads((ROOT / LOWER_BOUND_ARTIFACT).read_text())["lower_bound"])


def parse_solver_length(path: Path) -> int | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Length\s*=\s*(\d+)", text)
    return int(match.group(1)) if match else None


def append_record(record: dict[str, Any]) -> None:
    (ROOT / PROGRESS_PATH).parent.mkdir(parents=True, exist_ok=True)
    with (ROOT / PROGRESS_PATH).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def existing_done_ids() -> set[str]:
    path = ROOT / PROGRESS_PATH
    if not path.exists():
        return set()
    done: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("status") in {"done", "failed", "timeout"}:
            done.add(str(record["job_id"]))
    return done


def write_par(path: Path, tour_path: Path, config: Config, seed: int) -> None:
    lines = [
        f"PROBLEM_FILE = {TSPLIB_PATH}",
        f"OUTPUT_TOUR_FILE = {tour_path}",
        f"SEED = {seed}",
        f"TRACE_LEVEL = {TRACE_LEVEL}",
    ]
    lines += [f"{key} = {value}" for key, value in config.parameters]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_job(config: Config, seed: int, matrix: list[list[int]], timeout_seconds: float) -> dict[str, Any]:
    job_id = f"{config.config_id}__seed_{seed}"
    par = Path(f"data/processed/lkh-step13-{config.config_id}-seed-{seed}.par")
    tour_file = Path(f"data/processed/lkh-step13-{config.config_id}-seed-{seed}.tour")
    write_par(ROOT / par, tour_file, config, seed)
    command = [str(ROOT / LKH_BINARY), str(ROOT / par)]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_seconds,
        check=True,
    )
    runtime = time.perf_counter() - started
    tour = parse_tsplib_tour(ROOT / tour_file)
    validate_tour(tour, len(matrix))
    verified_length = tour_length(matrix, tour, validate=True)
    solver_length = parse_solver_length(ROOT / tour_file) or verified_length
    if solver_length != verified_length:
        raise AssertionError(f"solver/project length mismatch: {solver_length} != {verified_length}")
    return {
        "job_id": job_id,
        "config_id": config.config_id,
        "seed": seed,
        "status": "done",
        "solver_length": solver_length,
        "verified_length": verified_length,
        "runtime_seconds": round(runtime, 6),
        "parameters": dict(config.parameters),
        "parameter_file": str(par),
        "output_tour_file": str(tour_file),
        "command": " ".join(command),
        "tour": tour,
        "lkh_stdout_tail": "\n".join(completed.stdout.strip().splitlines()[-10:]),
        "created_at": datetime.now(UTC).isoformat(),
    }


def compact(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k not in {"tour", "lkh_stdout_tail"}}


def best_payload(record: dict[str, Any], lower_bound: float) -> dict[str, Any]:
    length = int(record["verified_length"])
    gap = length - lower_bound
    return {
        "type": "upper_bound",
        "algorithm": "lkh_2_0_11_targeted_wave",
        "length": length,
        "verified_length": length,
        "previous_upper_bound": CURRENT_UPPER_BOUND,
        "lower_bound": lower_bound,
        "absolute_gap": gap,
        "relative_gap_to_lower": gap / lower_bound,
        "relative_gap_to_upper": gap / length,
        "input_matrix": str(CHALLENGE_MATRIX_PATH),
        "tsplib_file": str(TSPLIB_PATH),
        "tour": record["tour"],
        "verification": "parse_tsplib_tour + validate_tour + tour_length(matrix, tour, validate=True)",
        "command": record["command"],
        "parameters": record["parameters"],
        "seed": record["seed"],
        "runtime_seconds": record["runtime_seconds"],
        "parameter_file": record["parameter_file"],
        "output_tour_file": record["output_tour_file"],
        "created_at": datetime.now(UTC).isoformat(),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs")
    parser.add_argument("--seeds", default="1-10")
    parser.add_argument("--job-timeout-minutes", type=float, default=20.0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    if not (ROOT / LKH_BINARY).exists():
        raise FileNotFoundError(LKH_BINARY)
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    write_explicit_tsplib(data.matrix, ROOT / TSPLIB_PATH, name="tsp_1114_challenge")
    configs = selected_configs(args.configs)
    seeds = parse_seed_spec(args.seeds)
    done = existing_done_ids() if args.resume else set()
    lower_bound = load_lower_bound()
    records: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for config in configs:
        for seed in seeds:
            job_id = f"{config.config_id}__seed_{seed}"
            if job_id in done:
                continue
            try:
                record = run_job(config, seed, data.matrix, args.job_timeout_minutes * 60)
            except subprocess.TimeoutExpired as exc:
                record = {"job_id": job_id, "config_id": config.config_id, "seed": seed, "status": "timeout", "error": repr(exc), "created_at": datetime.now(UTC).isoformat()}
            except Exception as exc:
                record = {"job_id": job_id, "config_id": config.config_id, "seed": seed, "status": "failed", "error": repr(exc), "created_at": datetime.now(UTC).isoformat()}
            records.append(record)
            append_record(compact(record))
            if record.get("status") == "done" and (best is None or int(record["verified_length"]) < int(best["verified_length"])):
                best = record
            print(f"{job_id} {record.get('status')} len={record.get('verified_length')} best={best.get('verified_length') if best else None}", flush=True)
            if record.get("status") == "done" and int(record["verified_length"]) < CURRENT_UPPER_BOUND:
                payload = best_payload(record, lower_bound)
                (ROOT / BEST_OUTPUT_PATH).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                break
    payload = {
        "algorithm": "lkh_2_0_11_targeted_wave",
        "input_matrix": str(CHALLENGE_MATRIX_PATH),
        "configs": [{"config_id": c.config_id, "parameters": dict(c.parameters)} for c in configs],
        "seeds": args.seeds,
        "records": [compact(r) for r in records],
        "best_verified_length": int(best["verified_length"]) if best else None,
        "improved_current_upper_bound": bool(best and int(best["verified_length"]) < CURRENT_UPPER_BOUND),
        "lower_bound": lower_bound,
        "created_at": datetime.now(UTC).isoformat(),
    }
    (ROOT / RUN_OUTPUT_PATH).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output={RUN_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
