from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.step12_lkh_portfolio import (
    BEST_OUTPUT_PATH,
    CURRENT_UPPER_BOUND,
    PROGRESS_PATH,
    RESULT_OUTPUT_PATH,
    Config,
    Job,
    append_ledger_record,
    best_artifact_payload,
    best_output_path_for_length,
    build_jobs,
    calibration_payload,
    completed_job_ids,
    default_configs,
    estimate_eta_seconds,
    format_duration,
    html_report,
    job_id,
    ledger_record,
    markdown_report,
    parse_seed_spec,
    plan_remaining_jobs,
    read_ledger_records,
    records_for_jobs,
    result_payload,
    runtime_stats,
    should_start_next_job,
)


def test_default_configs_and_seed_parser_build_deterministic_jobs():
    configs = default_configs()
    assert [config.config_id for config in configs] == [
        "A_default_r3",
        "B_default_r5",
        "C_trials3000_r3",
        "D_trials5000_r3",
        "E_patch_r3",
        "F_move5_r3",
    ]
    assert parse_seed_spec("1-3") == [1, 2, 3]
    assert parse_seed_spec("1,3,7") == [1, 3, 7]

    jobs = build_jobs(configs[:2], [1, 2])

    assert len(jobs) == 4
    assert [job.job_id for job in jobs] == [
        "A_default_r3__seed_1",
        "A_default_r3__seed_2",
        "B_default_r5__seed_1",
        "B_default_r5__seed_2",
    ]
    assert job_id("C_trials3000_r3", 8) == "C_trials3000_r3__seed_8"


def test_runtime_stats_eta_budget_and_duration_formatting():
    records = [
        {"status": "done", "runtime_seconds": 10.0},
        {"status": "done", "runtime_seconds": 20.0},
        {"status": "failed", "runtime_seconds": 5.0},
    ]

    stats = runtime_stats(records)

    assert stats["completed_count"] == 2
    assert stats["avg_seconds"] == 15.0
    assert estimate_eta_seconds(completed=2, total=5, avg_seconds=15.0) == 45.0
    assert should_start_next_job(elapsed_seconds=50.0, budget_seconds=100.0, estimated_job_seconds=40.0)
    assert not should_start_next_job(elapsed_seconds=70.0, budget_seconds=100.0, estimated_job_seconds=40.0)
    assert format_duration(3661.2) == "01:01:01"


def test_jsonl_ledger_resume_and_best_reconstruction(tmp_path: Path):
    ledger = tmp_path / "progress.jsonl"
    append_ledger_record(ledger, {"job_id": "a", "status": "done", "verified_length": 73934})
    append_ledger_record(ledger, {"job_id": "b", "status": "timeout", "error": "expired"})

    records = read_ledger_records(ledger)

    assert records == [
        {"job_id": "a", "status": "done", "verified_length": 73934},
        {"job_id": "b", "status": "timeout", "error": "expired"},
    ]
    assert completed_job_ids(records) == {"a", "b"}

    jobs = [
        Job(config=Config("A", {"RUNS": 3}), seed=1, job_index=1, jobs_total=2),
        Job(config=Config("B", {"RUNS": 3}), seed=2, job_index=2, jobs_total=2),
    ]
    remaining = plan_remaining_jobs(jobs, records, resume=True, force=False, ledger_exists=True)
    assert [job.job_id for job in remaining] == ["A__seed_1", "B__seed_2"]

    with pytest.raises(FileExistsError):
        plan_remaining_jobs(jobs, records, resume=False, force=False, ledger_exists=True)

    assert len(plan_remaining_jobs(jobs, records, resume=False, force=True, ledger_exists=True)) == 2


def test_resume_skips_matching_completed_job_ids():
    jobs = [
        Job(config=Config("A", {"RUNS": 3}), seed=1, job_index=1, jobs_total=2),
        Job(config=Config("A", {"RUNS": 3}), seed=2, job_index=2, jobs_total=2),
    ]
    records = [{"job_id": "A__seed_1", "status": "done", "verified_length": 73934}]

    remaining = plan_remaining_jobs(jobs, records, resume=True, force=False, ledger_exists=True)

    assert [job.job_id for job in remaining] == ["A__seed_2"]


def test_best_artifact_policy_and_payload():
    job = Job(config=Config("A_default_r3", {"RUNS": 3}), seed=4, job_index=1, jobs_total=1)
    run_record = {
        "job_id": job.job_id,
        "config_id": job.config.config_id,
        "seed": 4,
        "parameters": {"RUNS": 3},
        "verified_length": 73933,
        "solver_length": 73933,
        "tour": [0, 2, 1],
        "parameter_file": "data/processed/a.par",
        "output_tour_file": "data/processed/a.tour",
        "command": "LKH a.par",
    }

    assert best_output_path_for_length(73934) is None
    assert best_output_path_for_length(73933) == BEST_OUTPUT_PATH

    payload = best_artifact_payload(run_record, lower_bound=65493.437369)

    assert payload["algorithm"] == "lkh_2_0_11_portfolio"
    assert payload["verified_length"] == 73933
    assert payload["previous_upper_bound"] == CURRENT_UPPER_BOUND
    assert payload["improvement"] == 1
    assert payload["config_id"] == "A_default_r3"
    assert payload["seed"] == 4
    assert payload["parameters"] == {"RUNS": 3}
    assert payload["tour"] == [0, 2, 1]
    assert payload["absolute_gap"] == pytest.approx(8439.562631)


def test_ledger_record_is_compact_but_keeps_progress_fields():
    full_record = {
        "job_id": "A__seed_1",
        "job_index": 1,
        "jobs_total": 120,
        "config_id": "A",
        "seed": 1,
        "status": "done",
        "solver_length": 73934,
        "verified_length": 73934,
        "best_so_far": 73934,
        "runtime_seconds": 10.0,
        "elapsed_seconds": 10.0,
        "eta_seconds": 1190.0,
        "tour": [0, 2, 1],
        "lkh_stdout_tail": "verbose solver output",
        "command": "LKH a.par",
        "parameter_file": "a.par",
        "output_tour_file": "a.tour",
    }

    compact = ledger_record(full_record)

    assert compact["job_id"] == "A__seed_1"
    assert compact["jobs_total"] == 120
    assert compact["verified_length"] == 73934
    assert compact["parameter_file"] == "a.par"
    assert "tour" not in compact
    assert "lkh_stdout_tail" not in compact
    assert "command" not in compact

def test_result_and_calibration_payloads_are_compact():
    records = [
        {
            "job_id": "A__seed_1",
            "config_id": "A",
            "seed": 1,
            "status": "done",
            "verified_length": 73934,
            "runtime_seconds": 10.0,
        },
        {
            "job_id": "B__seed_1",
            "config_id": "B",
            "seed": 1,
            "status": "failed",
            "runtime_seconds": 5.0,
            "error": "boom",
        },
    ]
    configs = [Config("A", {"RUNS": 3}), Config("B", {"RUNS": 5})]

    payload = result_payload(
        records=records,
        configs=configs,
        seed_spec="1",
        command="cmd",
        time_budget_hours=2.0,
        job_timeout_minutes=20.0,
        lower_bound=65493.437369,
        jobs_planned=120,
    )

    assert payload["algorithm"] == "lkh_2_0_11_portfolio"
    assert payload["jobs_planned"] == 120
    assert payload["jobs_completed"] == 1
    assert payload["jobs_failed"] == 1
    assert payload["best_verified_length"] == 73934
    assert payload["improved_current_upper_bound"] is False
    assert payload["length_distribution"] == {"73934": 1}
    assert payload["progress_ledger"] == str(PROGRESS_PATH)
    assert payload["html_report"] == "results/runs/step12-lkh-portfolio-report.html"

    calibration = calibration_payload(records[:1], configs=configs, seed_spec="1-20", requested_jobs_total=120)
    assert calibration["avg_seconds_per_job"] == 10.0
    assert calibration["estimated_total_seconds"] == 1200.0
    assert calibration["requested_jobs_total"] == 120


def test_markdown_and_html_reports_include_core_tables():
    payload = {
        "algorithm": "lkh_2_0_11_portfolio",
        "command": "python experiments/step12_lkh_portfolio.py --seeds 1",
        "seed_spec": "1",
        "jobs_planned": 2,
        "jobs_completed": 2,
        "jobs_failed": 0,
        "jobs_timeout": 0,
        "best_verified_length": 73934,
        "best_config_id": "A_default_r3",
        "best_seed": 1,
        "improved_current_upper_bound": False,
        "length_distribution": {"73934": 1, "73941": 1},
        "runtime_by_config": {"A_default_r3": {"count": 2, "avg_seconds": 12.5}},
        "records": [
            {"job_id": "A_default_r3__seed_1", "config_id": "A_default_r3", "seed": 1, "status": "done", "verified_length": 73934, "runtime_seconds": 10.0},
            {"job_id": "A_default_r3__seed_2", "config_id": "A_default_r3", "seed": 2, "status": "done", "verified_length": 73941, "runtime_seconds": 15.0},
        ],
    }

    md = markdown_report(payload)
    html = html_report(payload)

    assert "# Step 12 — LKH portfolio search" in md
    assert "best_verified_length: 73934" in md
    assert "improved_current_upper_bound: false" in md
    assert "73934: 1" in md
    assert "<h1>Step 12 — LKH portfolio report</h1>" in html
    assert "Config × seed results" in html
    assert "Length distribution" in html
    assert "Runtime by config" in html
    assert "A_default_r3__seed_1" in html


def test_records_for_jobs_filters_unrelated_old_ledger_rows_and_dedupes_latest():
    jobs = [
        Job(config=Config("A", {"RUNS": 3}), seed=1, job_index=1, jobs_total=2),
        Job(config=Config("A", {"RUNS": 3}), seed=2, job_index=2, jobs_total=2),
    ]
    records = [
        {"job_id": "A__seed_1", "status": "done", "verified_length": 74000, "created_at": "old"},
        {"job_id": "B__seed_1", "status": "done", "verified_length": 73900, "created_at": "unrelated"},
        {"job_id": "A__seed_1", "status": "done", "verified_length": 73934, "created_at": "new"},
        {"job_id": "A__seed_2", "status": "timeout", "error": "expired"},
    ]

    filtered = records_for_jobs(records, jobs)

    assert filtered == [
        {"job_id": "A__seed_1", "status": "done", "verified_length": 73934, "created_at": "new"},
        {"job_id": "A__seed_2", "status": "timeout", "error": "expired"},
    ]


def test_expected_output_paths_are_project_relative():
    assert RESULT_OUTPUT_PATH == Path("results/runs/step12-lkh-portfolio.json")
    assert PROGRESS_PATH == Path("results/runs/step12-lkh-portfolio-progress.jsonl")
    assert BEST_OUTPUT_PATH == Path("results/best/step12-lkh-portfolio-best.json")
