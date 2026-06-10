from __future__ import annotations

from pathlib import Path

from src.integrations.concorde import (
    ConcordeLogSummary,
    choose_concorde_lower_bound,
    parse_concorde_log,
    verify_tsplib_full_matrix_mapping,
)
from src.io.tsplib import write_explicit_tsplib


CURRENT_LOWER_BOUND = 72711.81768955325
CURRENT_UPPER_BOUND = 73934


def test_parse_concorde_log_extracts_lower_upper_exact_and_lp_shape(tmp_path: Path) -> None:
    log = tmp_path / "concorde.log"
    log.write_text(
        "some setup\n"
        "Final lower bound 72800.125000, upper bound 73934.000000\n"
        "Exact lower bound: 72801.500000\n"
        "Final LP has 1200 rows, 620241 columns, 1800000 nonzeros\n",
        encoding="utf-8",
    )

    summary = parse_concorde_log(log)

    assert summary == ConcordeLogSummary(
        final_lower_bound=72800.125,
        final_upper_bound=73934.0,
        exact_lower_bound=72801.5,
        lp_rows=1200,
        lp_columns=620241,
        lp_nonzeros=1800000,
        optimal_solution=None,
        branch_and_bound_nodes=None,
    )


def test_choose_concorde_lower_bound_prefers_exact_when_present() -> None:
    summary = ConcordeLogSummary(
        final_lower_bound=72800.125,
        final_upper_bound=73934.0,
        exact_lower_bound=72801.5,
        lp_rows=None,
        lp_columns=None,
        lp_nonzeros=None,
        optimal_solution=None,
        branch_and_bound_nodes=None,
    )

    assert choose_concorde_lower_bound(summary) == 72801.5


def test_choose_concorde_lower_bound_rejects_missing_bound() -> None:
    summary = ConcordeLogSummary(
        final_lower_bound=None,
        final_upper_bound=None,
        exact_lower_bound=None,
        lp_rows=None,
        lp_columns=None,
        lp_nonzeros=None,
        optimal_solution=None,
        branch_and_bound_nodes=None,
    )

    try:
        choose_concorde_lower_bound(summary)
    except ValueError as exc:
        assert "no Concorde lower-bound field" in str(exc)
    else:
        raise AssertionError("missing lower bound was accepted")


def test_verify_tsplib_full_matrix_mapping_roundtrips_project_matrix(tmp_path: Path) -> None:
    matrix = [
        [0, 4, 7],
        [4, 0, 2],
        [7, 2, 0],
    ]
    tsplib = tmp_path / "tiny.tsp"
    write_explicit_tsplib(matrix, tsplib, name="tiny")

    verification = verify_tsplib_full_matrix_mapping(matrix, tsplib)

    assert verification == {
        "format": "TSPLIB_EXPLICIT_FULL_MATRIX",
        "dimension": 3,
        "entries_checked": 9,
        "matches_source_matrix": True,
    }


def test_review_gate_accepts_only_strict_lb_improvement_under_ub() -> None:
    improved = ConcordeLogSummary(
        final_lower_bound=72800.0,
        final_upper_bound=73934.0,
        exact_lower_bound=None,
        lp_rows=1,
        lp_columns=2,
        lp_nonzeros=3,
        optimal_solution=None,
        branch_and_bound_nodes=None,
    )
    not_improved = ConcordeLogSummary(
        final_lower_bound=CURRENT_LOWER_BOUND,
        final_upper_bound=73934.0,
        exact_lower_bound=None,
        lp_rows=None,
        lp_columns=None,
        lp_nonzeros=None,
        optimal_solution=None,
        branch_and_bound_nodes=None,
    )
    impossible = ConcordeLogSummary(
        final_lower_bound=74000.0,
        final_upper_bound=73934.0,
        exact_lower_bound=None,
        lp_rows=None,
        lp_columns=None,
        lp_nonzeros=None,
        optimal_solution=None,
        branch_and_bound_nodes=None,
    )

    assert improved.review_decision(CURRENT_LOWER_BOUND, CURRENT_UPPER_BOUND)["decision"] == "promote"
    assert not_improved.review_decision(CURRENT_LOWER_BOUND, CURRENT_UPPER_BOUND)["decision"] == "reject_no_improvement"
    assert impossible.review_decision(CURRENT_LOWER_BOUND, CURRENT_UPPER_BOUND)["decision"] == "reject_invalid_above_upper_bound"
