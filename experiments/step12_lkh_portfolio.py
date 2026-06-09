#!/usr/bin/env python3
"""Step 12: bounded LKH tuning portfolio with ETA, resume, and reports."""

from __future__ import annotations

import argparse
import html
import json
import re
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
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

ALGORITHM = "lkh_2_0_11_portfolio"
CURRENT_UPPER_BOUND = 73934
LOWER_BOUND_ARTIFACT = Path("results/best/step9-held-karp-one-tree.json")
LKH_BINARY = Path("tools/LKH-2.0.11/LKH")
TSPLIB_PATH = Path("data/processed/challenge-full-matrix.tsp")
TSPLIB_NAME = "tsp_1114_challenge"
TRACE_LEVEL = 1

BEST_OUTPUT_PATH = Path("results/best/step12-lkh-portfolio-best.json")
PROGRESS_PATH = Path("results/runs/step12-lkh-portfolio-progress.jsonl")
RESULT_OUTPUT_PATH = Path("results/runs/step12-lkh-portfolio.json")
HTML_REPORT_PATH = Path("results/runs/step12-lkh-portfolio-report.html")
MARKDOWN_REPORT_PATH = Path("notes/14-step12-lkh-portfolio.md")
CALIBRATION_OUTPUT_PATH = Path("results/runs/step12-lkh-portfolio-calibration.json")


@dataclass(frozen=True)
class Config:
    config_id: str
    parameters: dict[str, int]


@dataclass(frozen=True)
class Job:
    config: Config
    seed: int
    job_index: int
    jobs_total: int

    @property
    def job_id(self) -> str:
        return job_id(self.config.config_id, self.seed)


def default_configs() -> list[Config]:
    return [
        Config("A_default_r3", {"RUNS": 3}),
        Config("B_default_r5", {"RUNS": 5}),
        Config("C_trials3000_r3", {"RUNS": 3, "MAX_TRIALS": 3000}),
        Config("D_trials5000_r3", {"RUNS": 3, "MAX_TRIALS": 5000}),
        Config("E_patch_r3", {"RUNS": 3, "PATCHING_C": 3, "PATCHING_A": 2}),
        Config("F_move5_r3", {"RUNS": 3, "MOVE_TYPE": 5}),
    ]


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


def parse_config_spec(config_spec: str | None) -> list[Config]:
    configs = default_configs()
    if not config_spec:
        return configs
    by_id = {config.config_id: config for config in configs}
    selected: list[Config] = []
    for token in config_spec.split(","):
        config_id = token.strip()
        if not config_id:
            continue
        if config_id not in by_id:
            raise ValueError(f"unknown config id: {config_id}")
        selected.append(by_id[config_id])
    if not selected:
        raise ValueError("at least one config is required")
    return selected


def job_id(config_id: str, seed: int) -> str:
    return f"{config_id}__seed_{seed}"


def build_jobs(configs: list[Config], seeds: list[int]) -> list[Job]:
    total = len(configs) * len(seeds)
    jobs: list[Job] = []
    index = 1
    for config in configs:
        for seed in seeds:
            jobs.append(Job(config=config, seed=seed, job_index=index, jobs_total=total))
            index += 1
    return jobs


def runtime_stats(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    done_runtimes = [float(record["runtime_seconds"]) for record in records if record.get("status") == "done"]
    if not done_runtimes:
        return {"completed_count": 0, "avg_seconds": None, "min_seconds": None, "max_seconds": None}
    return {
        "completed_count": len(done_runtimes),
        "avg_seconds": sum(done_runtimes) / len(done_runtimes),
        "min_seconds": min(done_runtimes),
        "max_seconds": max(done_runtimes),
    }


def estimate_eta_seconds(*, completed: int, total: int, avg_seconds: float | None) -> float | None:
    if avg_seconds is None or completed >= total:
        return 0.0 if completed >= total else None
    return (total - completed) * avg_seconds


def should_start_next_job(
    *,
    elapsed_seconds: float,
    budget_seconds: float | None,
    estimated_job_seconds: float | None,
) -> bool:
    if budget_seconds is None:
        return True
    estimate = estimated_job_seconds if estimated_job_seconds is not None else 0.0
    return elapsed_seconds + estimate <= budget_seconds


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    whole = max(0, int(seconds))
    hours, remainder = divmod(whole, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def append_ledger_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_ledger_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def completed_job_ids(records: list[dict[str, Any]]) -> set[str]:
    terminal = {"done", "failed", "timeout"}
    return {str(record["job_id"]) for record in records if record.get("status") in terminal}


def records_for_jobs(records: list[dict[str, Any]], jobs: list[Job]) -> list[dict[str, Any]]:
    """Return the latest terminal ledger record for each requested job, in job order."""

    wanted = {job.job_id for job in jobs}
    latest_by_id: dict[str, dict[str, Any]] = {}
    terminal_statuses = {"done", "failed", "timeout"}
    for record in records:
        record_id = str(record.get("job_id", ""))
        if record_id in wanted and record.get("status") in terminal_statuses:
            latest_by_id[record_id] = record
    return [latest_by_id[job.job_id] for job in jobs if job.job_id in latest_by_id]


def plan_remaining_jobs(
    jobs: list[Job],
    records: list[dict[str, Any]],
    *,
    resume: bool,
    force: bool,
    ledger_exists: bool,
) -> list[Job]:
    if ledger_exists and not resume and not force:
        raise FileExistsError(f"progress ledger exists: {PROGRESS_PATH}; use --resume or --force")
    if not resume:
        return jobs
    done_ids = completed_job_ids(records)
    return [job for job in jobs if job.job_id not in done_ids]


def best_output_path_for_length(verified_length: int) -> Path | None:
    if verified_length < CURRENT_UPPER_BOUND:
        return BEST_OUTPUT_PATH
    return None


def best_done_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    done = [record for record in records if record.get("status") == "done" and "verified_length" in record]
    if not done:
        return None
    return min(done, key=lambda record: int(record["verified_length"]))


def load_lower_bound() -> float:
    return float(json.loads((ROOT / LOWER_BOUND_ARTIFACT).read_text(encoding="utf-8"))["lower_bound"])


def best_artifact_payload(run_record: dict[str, Any], *, lower_bound: float) -> dict[str, Any]:
    verified_length = int(run_record["verified_length"])
    absolute_gap = verified_length - lower_bound
    return {
        "algorithm": ALGORITHM,
        "input_file": str(CHALLENGE_MATRIX_PATH),
        "tsplib_file": str(TSPLIB_PATH),
        "n": 1114,
        "config_id": run_record["config_id"],
        "seed": run_record["seed"],
        "parameters": run_record["parameters"],
        "solver_length": run_record.get("solver_length"),
        "verified_length": verified_length,
        "previous_upper_bound": CURRENT_UPPER_BOUND,
        "improvement": CURRENT_UPPER_BOUND - verified_length,
        "lower_bound": lower_bound,
        "absolute_gap": absolute_gap,
        "relative_gap": absolute_gap / verified_length,
        "tour": run_record["tour"],
        "parameter_file": run_record["parameter_file"],
        "output_tour_file": run_record["output_tour_file"],
        "command": run_record["command"],
        "created_at": datetime.now(UTC).isoformat(),
    }


def result_payload(
    *,
    records: list[dict[str, Any]],
    configs: list[Config],
    seed_spec: str,
    command: str,
    time_budget_hours: float | None,
    job_timeout_minutes: float,
    lower_bound: float,
) -> dict[str, Any]:
    done = [record for record in records if record.get("status") == "done"]
    failed = [record for record in records if record.get("status") == "failed"]
    timed_out = [record for record in records if record.get("status") == "timeout"]
    best = best_done_record(records)
    best_length = int(best["verified_length"]) if best else None
    distribution = Counter(str(record["verified_length"]) for record in done)
    runtime_by_config = summarize_runtime_by_config(done)
    return {
        "algorithm": ALGORITHM,
        "command": command,
        "input_file": str(CHALLENGE_MATRIX_PATH),
        "tsplib_file": str(TSPLIB_PATH),
        "configs": [{"config_id": config.config_id, "parameters": config.parameters} for config in configs],
        "seed_spec": seed_spec,
        "time_budget_hours": time_budget_hours,
        "job_timeout_minutes": job_timeout_minutes,
        "jobs_planned": len(records),
        "jobs_completed": len(done),
        "jobs_failed": len(failed),
        "jobs_timeout": len(timed_out),
        "best_verified_length": best_length,
        "best_config_id": best.get("config_id") if best else None,
        "best_seed": best.get("seed") if best else None,
        "best_record": compact_record(best) if best else None,
        "improved_current_upper_bound": bool(best_length is not None and best_length < CURRENT_UPPER_BOUND),
        "improvement": CURRENT_UPPER_BOUND - best_length if best_length is not None else None,
        "lower_bound": lower_bound,
        "absolute_gap": best_length - lower_bound if best_length is not None else None,
        "relative_gap": (best_length - lower_bound) / best_length if best_length else None,
        "length_distribution": dict(sorted(distribution.items(), key=lambda item: int(item[0]))),
        "runtime_by_config": runtime_by_config,
        "records": [compact_record(record) for record in records],
        "progress_ledger": str(PROGRESS_PATH),
        "html_report": str(HTML_REPORT_PATH),
        "created_at": datetime.now(UTC).isoformat(),
    }


def calibration_payload(
    records: list[dict[str, Any]],
    *,
    configs: list[Config],
    seed_spec: str,
    requested_jobs_total: int,
) -> dict[str, Any]:
    stats = runtime_stats(records)
    avg = stats["avg_seconds"]
    return {
        "algorithm": ALGORITHM,
        "mode": "calibration",
        "configs": [{"config_id": config.config_id, "parameters": config.parameters} for config in configs],
        "seed_spec": seed_spec,
        "calibration_jobs_completed": stats["completed_count"],
        "avg_seconds_per_job": avg,
        "estimated_total_seconds": requested_jobs_total * avg if avg is not None else None,
        "estimated_total_hhmmss": format_duration(requested_jobs_total * avg if avg is not None else None),
        "requested_jobs_total": requested_jobs_total,
        "runtime_by_config": summarize_runtime_by_config([r for r in records if r.get("status") == "done"]),
        "records": [compact_record(record) for record in records],
        "created_at": datetime.now(UTC).isoformat(),
    }


def summarize_runtime_by_config(records: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[str(record["config_id"])].append(float(record["runtime_seconds"]))
    summary: dict[str, dict[str, float | int]] = {}
    for config_id, runtimes in sorted(grouped.items()):
        summary[config_id] = {
            "count": len(runtimes),
            "avg_seconds": sum(runtimes) / len(runtimes),
            "min_seconds": min(runtimes),
            "max_seconds": max(runtimes),
        }
        if len(runtimes) > 1:
            summary[config_id]["median_seconds"] = statistics.median(runtimes)
    return summary


def compact_record(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    keep = [
        "job_id",
        "job_index",
        "jobs_total",
        "config_id",
        "seed",
        "status",
        "solver_length",
        "verified_length",
        "best_so_far",
        "runtime_seconds",
        "elapsed_seconds",
        "eta_seconds",
        "parameter_file",
        "output_tour_file",
        "error",
        "created_at",
    ]
    return {key: record[key] for key in keep if key in record}


def markdown_report(payload: dict[str, Any]) -> str:
    dist = payload.get("length_distribution", {})
    runtime = payload.get("runtime_by_config", {})
    lines = [
        "# Step 12 — LKH portfolio search",
        "",
        "## Command",
        "",
        "```bash",
        str(payload.get("command", "")),
        "```",
        "",
        "## Summary",
        "",
        "```txt",
        f"best_verified_length: {payload.get('best_verified_length')}",
        f"best_config_id: {payload.get('best_config_id')}",
        f"best_seed: {payload.get('best_seed')}",
        f"improved_current_upper_bound: {str(payload.get('improved_current_upper_bound')).lower()}",
        f"jobs_completed: {payload.get('jobs_completed')}",
        f"jobs_failed: {payload.get('jobs_failed')}",
        f"jobs_timeout: {payload.get('jobs_timeout')}",
        "```",
        "",
        "## Length distribution",
        "",
    ]
    if dist:
        lines.extend(f"- {length}: {count}" for length, count in dist.items())
    else:
        lines.append("- no completed runs")
    lines.extend(["", "## Runtime by config", ""])
    if runtime:
        lines.append("| config | count | avg seconds | min | max |")
        lines.append("|---|---:|---:|---:|---:|")
        for config_id, stats in runtime.items():
            avg = float(stats.get("avg_seconds", 0.0))
            min_seconds = float(stats.get("min_seconds", avg))
            max_seconds = float(stats.get("max_seconds", avg))
            lines.append(
                f"| {config_id} | {stats['count']} | {avg:.3f} | "
                f"{min_seconds:.3f} | {max_seconds:.3f} |"
            )
    else:
        lines.append("No completed runs yet.")
    lines.extend(
        [
            "",
            "## Current interval",
            "",
            "```txt",
            f"{float(payload.get('lower_bound') or 65493.437369):.6f} <= OPT <= {payload.get('best_verified_length') or CURRENT_UPPER_BOUND}",
            "```",
            "",
            "## Recommended next step",
            "",
            "If no improvement was found, use the runtime table to select the best 1-2 configs for a longer targeted wave, or stop upper-bound search and prepare the final explanation.",
            "",
        ]
    )
    return "\n".join(lines)


def html_report(payload: dict[str, Any]) -> str:
    rows = payload.get("records", [])
    dist = payload.get("length_distribution", {})
    runtime = payload.get("runtime_by_config", {})
    row_html = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('job_id', '')))}</td>"
        f"<td>{html.escape(str(row.get('config_id', '')))}</td>"
        f"<td>{html.escape(str(row.get('seed', '')))}</td>"
        f"<td>{html.escape(str(row.get('status', '')))}</td>"
        f"<td>{html.escape(str(row.get('verified_length', '')))}</td>"
        f"<td>{float(row.get('runtime_seconds', 0) or 0):.3f}</td>"
        "</tr>"
        for row in rows
    )
    dist_html = "\n".join(
        f"<tr><td>{html.escape(str(length))}</td><td>{count}</td></tr>" for length, count in dist.items()
    )
    runtime_html = "\n".join(
        f"<tr><td>{html.escape(str(config_id))}</td><td>{stats['count']}</td>"
        f"<td>{float(stats.get('avg_seconds', 0.0)):.3f}</td>"
        f"<td>{float(stats.get('min_seconds', stats.get('avg_seconds', 0.0))):.3f}</td>"
        f"<td>{float(stats.get('max_seconds', stats.get('avg_seconds', 0.0))):.3f}</td></tr>"
        for config_id, stats in runtime.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Step 12 LKH portfolio report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; background: #f8fafc; color: #111827; }}
.card {{ display: inline-block; padding: 14px 18px; margin: 0 12px 12px 0; background: #fff; border: 1px solid #d1d5db; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 28px; background: #fff; }}
th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; text-align: left; font-size: 13px; }}
th {{ background: #e5e7eb; }}
code {{ background: #e5e7eb; padding: 2px 4px; }}
</style>
</head>
<body>
<h1>Step 12 — LKH portfolio report</h1>
<div class="card"><strong>Best</strong><br>{html.escape(str(payload.get('best_verified_length')))}</div>
<div class="card"><strong>Improved</strong><br>{html.escape(str(payload.get('improved_current_upper_bound')))}</div>
<div class="card"><strong>Completed</strong><br>{html.escape(str(payload.get('jobs_completed')))}</div>
<div class="card"><strong>Failed/timeout</strong><br>{html.escape(str(payload.get('jobs_failed')))} / {html.escape(str(payload.get('jobs_timeout')))}</div>
<p><strong>Command:</strong> <code>{html.escape(str(payload.get('command', '')))}</code></p>
<h2>Config × seed results</h2>
<table><thead><tr><th>job</th><th>config</th><th>seed</th><th>status</th><th>verified length</th><th>runtime s</th></tr></thead><tbody>
{row_html}
</tbody></table>
<h2>Length distribution</h2>
<table><thead><tr><th>length</th><th>count</th></tr></thead><tbody>
{dist_html}
</tbody></table>
<h2>Runtime by config</h2>
<table><thead><tr><th>config</th><th>count</th><th>avg s</th><th>min s</th><th>max s</th></tr></thead><tbody>
{runtime_html}
</tbody></table>
</body></html>
"""


def write_lkh_parameter_file(*, parameter_path: Path, problem_file: Path, output_tour_file: Path, job: Job) -> None:
    lines = [f"PROBLEM_FILE = {problem_file}", f"OUTPUT_TOUR_FILE = {output_tour_file}"]
    for key, value in job.config.parameters.items():
        lines.append(f"{key} = {value}")
    lines.extend([f"SEED = {job.seed}", f"TRACE_LEVEL = {TRACE_LEVEL}", ""])
    parameter_path.parent.mkdir(parents=True, exist_ok=True)
    parameter_path.write_text("\n".join(lines), encoding="utf-8")


def parse_solver_length(tour_file: Path) -> int | None:
    for line in tour_file.read_text(encoding="utf-8").splitlines():
        match = re.search(r"Length\s*=\s*(\d+)", line)
        if match:
            return int(match.group(1))
    return None


def run_lkh_job(*, job: Job, matrix: list[list[int]], timeout_seconds: float) -> dict[str, Any]:
    safe_config = job.config.config_id.replace("/", "_")
    parameter_path = Path(f"data/processed/lkh-step12-{safe_config}-seed-{job.seed}.par")
    output_tour_path = Path(f"data/processed/lkh-step12-{safe_config}-seed-{job.seed}.tour")
    write_lkh_parameter_file(
        parameter_path=ROOT / parameter_path,
        problem_file=TSPLIB_PATH,
        output_tour_file=output_tour_path,
        job=job,
    )
    command = [str(ROOT / LKH_BINARY), str(ROOT / parameter_path)]
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
    runtime_seconds = time.perf_counter() - started
    tour = parse_tsplib_tour(ROOT / output_tour_path)
    validate_tour(tour, len(matrix))
    verified_length = tour_length(matrix, tour, validate=True)
    solver_length = parse_solver_length(ROOT / output_tour_path) or verified_length
    if solver_length != verified_length:
        raise AssertionError(
            f"solver/project length mismatch for {job.job_id}: {solver_length} != {verified_length}"
        )
    return {
        "job_id": job.job_id,
        "job_index": job.job_index,
        "jobs_total": job.jobs_total,
        "config_id": job.config.config_id,
        "seed": job.seed,
        "status": "done",
        "solver_length": solver_length,
        "verified_length": verified_length,
        "runtime_seconds": round(runtime_seconds, 6),
        "parameter_file": str(parameter_path),
        "output_tour_file": str(output_tour_path),
        "command": " ".join(command),
        "parameters": job.config.parameters,
        "tour": tour,
        "lkh_stdout_tail": "\n".join(completed.stdout.strip().splitlines()[-10:]),
    }


def enrich_record(
    record: dict[str, Any],
    *,
    records_so_far: list[dict[str, Any]],
    started_at: float,
) -> dict[str, Any]:
    all_records = records_so_far + [record]
    best = best_done_record(all_records)
    stats = runtime_stats(all_records)
    elapsed = time.perf_counter() - started_at
    eta = estimate_eta_seconds(
        completed=len(all_records),
        total=int(record.get("jobs_total", len(all_records))),
        avg_seconds=stats["avg_seconds"],
    )
    record["best_so_far"] = int(best["verified_length"]) if best else CURRENT_UPPER_BOUND
    record["elapsed_seconds"] = round(elapsed, 6)
    record["eta_seconds"] = round(float(eta), 6) if eta is not None else None
    record["created_at"] = datetime.now(UTC).isoformat()
    return record


def maybe_write_best_artifact(record: dict[str, Any], *, lower_bound: float) -> None:
    output_path = best_output_path_for_length(int(record.get("verified_length", CURRENT_UPPER_BOUND)))
    if output_path is None:
        return
    payload = best_artifact_payload(record, lower_bound=lower_bound)
    (ROOT / output_path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_progress(record: dict[str, Any], *, budget_seconds: float | None) -> None:
    elapsed = float(record.get("elapsed_seconds", 0.0))
    eta = record.get("eta_seconds")
    budget_left = None if budget_seconds is None else max(0.0, budget_seconds - elapsed)
    length = record.get("verified_length", record.get("error", "n/a"))
    print(
        f"[{record.get('job_index')}/{record.get('jobs_total')}] {record.get('config_id')} "
        f"seed={record.get('seed')} {record.get('status')} "
        f"{float(record.get('runtime_seconds', 0.0)):.1f}s len={length} best={record.get('best_so_far')}"
    )
    print(
        f"elapsed: {format_duration(elapsed)} | ETA: {format_duration(float(eta) if eta is not None else None)} | "
        f"budget left: {format_duration(budget_left)}"
    )


def write_run_artifacts(payload: dict[str, Any]) -> None:
    (ROOT / RESULT_OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / RESULT_OUTPUT_PATH).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / MARKDOWN_REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / MARKDOWN_REPORT_PATH).write_text(markdown_report(payload), encoding="utf-8")
    (ROOT / HTML_REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / HTML_REPORT_PATH).write_text(html_report(payload), encoding="utf-8")


def remove_old_outputs(*, keep_calibration: bool = False) -> None:
    paths = [PROGRESS_PATH, RESULT_OUTPUT_PATH, HTML_REPORT_PATH, BEST_OUTPUT_PATH]
    if not keep_calibration:
        paths.append(CALIBRATION_OUTPUT_PATH)
    for path in paths:
        full = ROOT / path
        if full.exists():
            full.unlink()


def run_jobs(
    *,
    jobs: list[Job],
    configs: list[Config],
    seed_spec: str,
    command: str,
    time_budget_hours: float | None,
    job_timeout_minutes: float,
    resume: bool,
    force: bool,
    calibrate: bool,
) -> list[dict[str, Any]]:
    if not (ROOT / LKH_BINARY).exists():
        raise FileNotFoundError(f"LKH binary not found: {LKH_BINARY}")
    ledger_exists = (ROOT / PROGRESS_PATH).exists()
    prior_records = read_ledger_records(ROOT / PROGRESS_PATH) if ledger_exists and resume else []
    if ledger_exists and force and not resume:
        remove_old_outputs(keep_calibration=not calibrate)
        prior_records = []
        ledger_exists = False
    remaining_jobs = plan_remaining_jobs(
        jobs,
        prior_records,
        resume=resume,
        force=force,
        ledger_exists=ledger_exists,
    )

    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    write_explicit_tsplib(data.matrix, ROOT / TSPLIB_PATH, name=TSPLIB_NAME)
    records = records_for_jobs(prior_records, jobs)
    started_at = time.perf_counter()
    budget_seconds = None if time_budget_hours is None else time_budget_hours * 3600.0
    timeout_seconds = job_timeout_minutes * 60.0
    print("Step 12 LKH Portfolio")
    print(f"jobs_total={len(jobs)} jobs_remaining={len(remaining_jobs)}")

    for job in remaining_jobs:
        stats = runtime_stats(records)
        elapsed = time.perf_counter() - started_at
        if not should_start_next_job(
            elapsed_seconds=elapsed,
            budget_seconds=budget_seconds,
            estimated_job_seconds=stats["avg_seconds"],
        ):
            print("time_budget_reached_before_next_job")
            break
        try:
            raw_record = run_lkh_job(job=job, matrix=data.matrix, timeout_seconds=timeout_seconds)
            record = enrich_record(raw_record, records_so_far=records, started_at=started_at)
            if not calibrate:
                maybe_write_best_artifact(record, lower_bound=load_lower_bound())
        except subprocess.TimeoutExpired as exc:
            raw_record = failure_record(job, status="timeout", error=repr(exc), runtime_seconds=timeout_seconds)
            record = enrich_record(raw_record, records_so_far=records, started_at=started_at)
        except Exception as exc:
            raw_record = failure_record(job, status="failed", error=repr(exc), runtime_seconds=0.0)
            record = enrich_record(raw_record, records_so_far=records, started_at=started_at)
        append_ledger_record(ROOT / PROGRESS_PATH, record)
        records.append(record)
        print_progress(record, budget_seconds=budget_seconds)
    return records


def failure_record(job: Job, *, status: str, error: str, runtime_seconds: float) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "job_index": job.job_index,
        "jobs_total": job.jobs_total,
        "config_id": job.config.config_id,
        "seed": job.seed,
        "status": status,
        "error": error,
        "runtime_seconds": runtime_seconds,
        "parameters": job.config.parameters,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configs", default=None, help="Comma-separated config ids; default all configs")
    parser.add_argument("--seeds", default="1-20", help="Seed list/range, e.g. 1-20 or 1,3,7")
    parser.add_argument("--time-budget-hours", type=float, default=None)
    parser.add_argument("--job-timeout-minutes", type=float, default=20.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args(argv)

    configs = parse_config_spec(args.configs)
    seeds = parse_seed_spec(args.seeds)
    jobs = build_jobs(configs, seeds)
    command = "python experiments/step12_lkh_portfolio.py " + " ".join(sys.argv[1:])
    records = run_jobs(
        jobs=jobs,
        configs=configs,
        seed_spec=args.seeds,
        command=command,
        time_budget_hours=args.time_budget_hours,
        job_timeout_minutes=args.job_timeout_minutes,
        resume=args.resume,
        force=args.force,
        calibrate=args.calibrate,
    )
    lower_bound = load_lower_bound()
    if args.calibrate:
        payload = calibration_payload(records, configs=configs, seed_spec=args.seeds, requested_jobs_total=len(jobs))
        (ROOT / CALIBRATION_OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / CALIBRATION_OUTPUT_PATH).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"calibration_avg_seconds_per_job={payload['avg_seconds_per_job']}")
        print(f"calibration_estimated_total={payload['estimated_total_hhmmss']}")
        print(f"output={CALIBRATION_OUTPUT_PATH}")
    else:
        payload = result_payload(
            records=records,
            configs=configs,
            seed_spec=args.seeds,
            command=command,
            time_budget_hours=args.time_budget_hours,
            job_timeout_minutes=args.job_timeout_minutes,
            lower_bound=lower_bound,
        )
        write_run_artifacts(payload)
        print(f"best_verified_length={payload['best_verified_length']}")
        print(f"improved_current_upper_bound={payload['improved_current_upper_bound']}")
        print(f"output={RESULT_OUTPUT_PATH}")
        print(f"html_report={HTML_REPORT_PATH}")


if __name__ == "__main__":
    main()
