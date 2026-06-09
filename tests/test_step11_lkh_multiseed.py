from __future__ import annotations

from pathlib import Path

from experiments.step11_lkh_multiseed import (
    BEST_OUTPUT_PATH,
    CURRENT_UPPER_BOUND,
    RUN_OUTPUT_PATH,
    choose_best_run,
    output_path_for_best_length,
    step11_payload,
)


def test_choose_best_run_uses_lowest_verified_length():
    runs = [
        {"seed": 1, "verified_length": 73934},
        {"seed": 2, "verified_length": 73890},
        {"seed": 3, "verified_length": 74100},
    ]

    assert choose_best_run(runs) == {"seed": 2, "verified_length": 73890}


def test_choose_best_run_requires_verified_project_length():
    runs = [
        {"seed": 1, "solver_length": 73000},
    ]

    try:
        choose_best_run(runs)
    except KeyError as exc:
        assert str(exc) == "'verified_length'"
    else:
        raise AssertionError("choose_best_run accepted a run without verified_length")


def test_output_path_policy_routes_only_improvements_to_best():
    assert output_path_for_best_length(73933) == BEST_OUTPUT_PATH
    assert output_path_for_best_length(CURRENT_UPPER_BOUND) == RUN_OUTPUT_PATH
    assert output_path_for_best_length(74000) == RUN_OUTPUT_PATH


def test_step11_payload_marks_non_improving_result_as_not_new_best():
    runs = [
        {
            "seed": 1,
            "solver_length": 73934,
            "verified_length": 73934,
            "runtime_seconds": 1.2,
            "parameter_file": "data/processed/lkh-step11-seed-1.par",
            "output_tour_file": "data/processed/lkh-step11-seed-1.tour",
            "command": "tools/LKH data/processed/lkh-step11-seed-1.par",
            "parameters": {"runs": 1, "seed": 1, "trace_level": 1},
        }
    ]

    payload = step11_payload(
        runs=runs,
        seed_spec="1",
        runs_per_seed=1,
        max_trials=None,
        lower_bound=65493.437369,
        command="python experiments/step11_lkh_multiseed.py --seeds 1 --runs 1",
    )

    assert payload["algorithm"] == "lkh_2_0_11_multiseed"
    assert payload["current_upper_bound"] == 73934
    assert payload["best_verified_length"] == 73934
    assert payload["best_seed"] == 1
    assert payload["improved_current_upper_bound"] is False
    assert payload["output_policy"] == str(RUN_OUTPUT_PATH)
    assert payload["runs_completed"] == 1
    assert payload["runs_failed"] == 0
    assert payload["lower_bound"] == 65493.437369
    assert payload["absolute_gap"] == 8440.562631
    assert payload["relative_gap"] == 8440.562631 / 73934
    assert payload["runs"][0]["verified_length"] == 73934
    assert "created_at" in payload


def test_step11_payload_marks_improving_result_as_new_best():
    runs = [
        {
            "seed": 7,
            "solver_length": 73888,
            "verified_length": 73888,
            "runtime_seconds": 2.4,
            "parameter_file": "data/processed/lkh-step11-seed-7.par",
            "output_tour_file": "data/processed/lkh-step11-seed-7.tour",
            "command": "tools/LKH data/processed/lkh-step11-seed-7.par",
            "parameters": {"runs": 1, "seed": 7, "trace_level": 1},
        }
    ]

    payload = step11_payload(
        runs=runs,
        seed_spec="7",
        runs_per_seed=1,
        max_trials=None,
        lower_bound=65493.437369,
        command="cmd",
    )

    assert payload["best_verified_length"] == 73888
    assert payload["improved_current_upper_bound"] is True
    assert payload["improvement"] == 46
    assert payload["output_policy"] == str(BEST_OUTPUT_PATH)


def test_step11_paths_are_project_relative():
    assert BEST_OUTPUT_PATH == Path("results/best/step11-lkh-multiseed-best.json")
    assert RUN_OUTPUT_PATH == Path("results/runs/step11-lkh-multiseed.json")
