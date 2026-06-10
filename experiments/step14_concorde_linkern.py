#!/usr/bin/env python3
"""Step 14: Concorde linkern upper-bound attempts with independent verification."""

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
from src.io.validation import validate_tour
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

CURRENT_UPPER_BOUND = 73934
LOWER_BOUND_ARTIFACT = Path("results/best/step9-held-karp-one-tree.json")
BASE_TOUR_ARTIFACT = Path("results/best/step6-lkh-best.json")
TSPLIB_PATH = Path("data/processed/challenge-full-matrix.tsp")
LINKERN_BINARY = Path("tools/concorde-build/LINKERN/linkern")
START_CYCLE = Path("data/processed/linkern-start-step6-lkh-best.cyc")
PROGRESS_PATH = Path("results/runs/step14-linkern-progress.jsonl")
RUN_OUTPUT_PATH = Path("results/runs/step14-linkern-wave.json")
BEST_OUTPUT_PATH = Path("results/best/step14-linkern-upper-bound.json")


@dataclass(frozen=True)
class Config:
    config_id: str
    args: tuple[str, ...]
    use_lkh_start: bool


def default_configs() -> list[Config]:
    return [
        Config("from_lkh_q3", tuple(), True),
        Config("from_lkh_a20", ("-a", "20"), True),
        Config("from_lkh_a50", ("-a", "50"), True),
        Config("random_q3", tuple(), False),
        Config("random_a20", ("-a", "20"), False),
    ]


def parse_seed_spec(spec: str) -> list[int]:
    seeds: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))
    return seeds


def selected_configs(spec: str | None) -> list[Config]:
    configs = default_configs()
    if not spec:
        return configs
    by_id = {c.config_id: c for c in configs}
    return [by_id[s.strip()] for s in spec.split(",") if s.strip()]


def write_start_cycle() -> None:
    artifact = json.loads((ROOT / BASE_TOUR_ARTIFACT).read_text(encoding="utf-8"))
    tour = artifact["tour"]
    (ROOT / START_CYCLE).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / START_CYCLE).write_text(str(len(tour)) + "\n" + " ".join(map(str, tour)) + "\n", encoding="utf-8")


def parse_linkern_cycle(path: Path) -> list[int]:
    nums = [int(x) for x in path.read_text(encoding="utf-8").split()]
    if not nums:
        raise ValueError(f"empty cycle file: {path}")
    n = nums[0]
    # Node-cycle format: n followed by n nodes.
    if len(nums) == n + 1:
        return nums[1:]
    # Edge-list format: n e followed by e triples (u, v, length).
    if len(nums) >= 2:
        e = nums[1]
        triples = nums[2:]
        if len(triples) == 3 * e:
            adj: list[list[int]] = [[] for _ in range(n)]
            for i in range(e):
                u, v, _w = triples[3 * i : 3 * i + 3]
                adj[u].append(v)
                adj[v].append(u)
            if any(len(a) != 2 for a in adj):
                raise ValueError("edge-list cycle is not 2-regular")
            tour = [0]
            prev = -1
            cur = 0
            for _ in range(n - 1):
                nxt = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
                tour.append(nxt)
                prev, cur = cur, nxt
            if tour[-1] not in adj[0]:
                raise ValueError("edge-list cycle does not close")
            return tour
    raise ValueError(f"unrecognized linkern cycle format: {path}")


def parse_best_from_stdout(stdout: str) -> int | None:
    matches = re.findall(r"Overall Best Cycle:\s*([0-9]+)", stdout)
    return int(matches[-1]) if matches else None


def append_record(record: dict[str, Any]) -> None:
    (ROOT / PROGRESS_PATH).parent.mkdir(parents=True, exist_ok=True)
    with (ROOT / PROGRESS_PATH).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def existing_done_ids() -> set[str]:
    if not (ROOT / PROGRESS_PATH).exists():
        return set()
    done: set[str] = set()
    for line in (ROOT / PROGRESS_PATH).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("status") in {"done", "failed", "timeout"}:
            done.add(record["job_id"])
    return done


def run_job(config: Config, seed: int, matrix: list[list[int]], timeout_seconds: float, run_kicks: int, time_bound: int) -> dict[str, Any]:
    job_id = f"{config.config_id}__seed_{seed}"
    out_cycle = Path(f"data/processed/linkern-step14-{config.config_id}-seed-{seed}.cyc")
    log_path = Path(f"results/runs/linkern-step14-{config.config_id}-seed-{seed}.log")
    cmd = [str(ROOT / LINKERN_BINARY), "-Q", "-s", str(seed), "-r", "1", "-R", str(run_kicks), "-t", str(time_bound), "-h", str(CURRENT_UPPER_BOUND - 1), *config.args]
    if config.use_lkh_start:
        cmd += ["-y", str(ROOT / START_CYCLE)]
    cmd += ["-o", str(ROOT / out_cycle), str(ROOT / TSPLIB_PATH)]
    started = time.perf_counter()
    completed = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout_seconds, check=False)
    runtime = time.perf_counter() - started
    (ROOT / log_path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / log_path).write_text(completed.stdout, encoding="utf-8")
    if completed.returncode not in (0, 1):
        raise RuntimeError(f"linkern failed with {completed.returncode}; see {log_path}")
    tour = parse_linkern_cycle(ROOT / out_cycle)
    validate_tour(tour, len(matrix))
    verified_length = tour_length(matrix, tour, validate=True)
    solver_length = parse_best_from_stdout(completed.stdout)
    if solver_length is not None and solver_length != verified_length:
        raise AssertionError(f"solver/project length mismatch: {solver_length} != {verified_length}")
    return {
        "job_id": job_id,
        "config_id": config.config_id,
        "seed": seed,
        "status": "done",
        "solver_length": solver_length,
        "verified_length": verified_length,
        "runtime_seconds": round(runtime, 6),
        "command": " ".join(cmd),
        "parameters": {"args": list(config.args), "use_lkh_start": config.use_lkh_start, "run_kicks": run_kicks, "time_bound_seconds": time_bound},
        "output_cycle_file": str(out_cycle),
        "log_file": str(log_path),
        "tour": tour,
        "created_at": datetime.now(UTC).isoformat(),
    }


def compact(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k != "tour"}


def load_lower_bound() -> float:
    return float(json.loads((ROOT / LOWER_BOUND_ARTIFACT).read_text(encoding="utf-8"))["lower_bound"])


def maybe_write_best(record: dict[str, Any], lower_bound: float) -> None:
    length = int(record["verified_length"])
    if length >= CURRENT_UPPER_BOUND:
        return
    gap = length - lower_bound
    payload = {
        "type": "upper_bound",
        "algorithm": "concorde_linkern_03_12_19",
        "length": length,
        "verified_length": length,
        "previous_upper_bound": CURRENT_UPPER_BOUND,
        "lower_bound": lower_bound,
        "absolute_gap": gap,
        "relative_gap_to_lower": gap / lower_bound,
        "input_matrix": str(CHALLENGE_MATRIX_PATH),
        "tsplib_file": str(TSPLIB_PATH),
        "tour": record["tour"],
        "verification": "parse_linkern_cycle + validate_tour + tour_length(matrix, tour, validate=True)",
        "source_record": compact(record),
        "created_at": datetime.now(UTC).isoformat(),
    }
    (ROOT / BEST_OUTPUT_PATH).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs")
    parser.add_argument("--seeds", default="1-20")
    parser.add_argument("--job-timeout-seconds", type=float, default=60.0)
    parser.add_argument("--time-bound-seconds", type=int, default=60)
    parser.add_argument("--run-kicks", type=int, default=1114)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    if not (ROOT / LINKERN_BINARY).exists():
        raise FileNotFoundError(LINKERN_BINARY)
    write_start_cycle()
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    lower_bound = load_lower_bound()
    done = existing_done_ids() if args.resume else set()
    records: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for config in selected_configs(args.configs):
        for seed in parse_seed_spec(args.seeds):
            job_id = f"{config.config_id}__seed_{seed}"
            if job_id in done:
                continue
            try:
                record = run_job(config, seed, data.matrix, args.job_timeout_seconds, args.run_kicks, args.time_bound_seconds)
            except subprocess.TimeoutExpired as exc:
                record = {"job_id": job_id, "config_id": config.config_id, "seed": seed, "status": "timeout", "error": repr(exc), "created_at": datetime.now(UTC).isoformat()}
            except Exception as exc:
                record = {"job_id": job_id, "config_id": config.config_id, "seed": seed, "status": "failed", "error": repr(exc), "created_at": datetime.now(UTC).isoformat()}
            records.append(record)
            append_record(compact(record))
            if record.get("status") == "done" and (best is None or int(record["verified_length"]) < int(best["verified_length"])):
                best = record
                maybe_write_best(record, lower_bound)
            print(f"{job_id} {record.get('status')} len={record.get('verified_length')} best={best.get('verified_length') if best else None}", flush=True)
            if record.get("status") == "done" and int(record["verified_length"]) < CURRENT_UPPER_BOUND:
                break
    payload = {
        "algorithm": "concorde_linkern_03_12_19",
        "input_matrix": str(CHALLENGE_MATRIX_PATH),
        "tsplib_file": str(TSPLIB_PATH),
        "linkern_binary": str(LINKERN_BINARY),
        "download_sha256": "c3650a59c8d57e0a00e81c1288b994a99c5aa03e5d96a314834c2d8f9505c724",
        "configs": [{"config_id": c.config_id, "args": list(c.args), "use_lkh_start": c.use_lkh_start} for c in selected_configs(args.configs)],
        "seeds": args.seeds,
        "records": [compact(r) for r in records],
        "best_verified_length": int(best["verified_length"]) if best else None,
        "improved_current_upper_bound": bool(best and int(best["verified_length"]) < CURRENT_UPPER_BOUND),
        "current_upper_bound": CURRENT_UPPER_BOUND,
        "lower_bound": lower_bound,
        "created_at": datetime.now(UTC).isoformat(),
    }
    (ROOT / RUN_OUTPUT_PATH).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output={RUN_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
