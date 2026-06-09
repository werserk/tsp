from __future__ import annotations

from pathlib import Path

from src.heuristics.restricted_three_opt import (
    RESTRICTED_THREE_OPT_ALGORITHM,
    RestrictedThreeOptResult,
    improve_tour_restricted_three_opt,
    restricted_three_opt_payload,
)


def test_restricted_three_opt_finds_better_segment_reconnection_from_candidate_cuts():
    matrix = _matrix_with_cheap_cycle([0, 3, 1, 2, 4, 5])
    initial_tour = [0, 1, 2, 3, 4, 5]

    result = improve_tour_restricted_three_opt(
        matrix,
        initial_tour,
        cut_positions=[1, 3, 4],
        max_passes=1,
    )

    assert result.algorithm == RESTRICTED_THREE_OPT_ALGORITHM
    assert result.initial_length > result.length
    assert result.length == 6
    assert result.tour == [0, 3, 1, 2, 4, 5]
    assert result.moves_applied == 1
    assert result.candidate_cut_count == 3


def test_restricted_three_opt_returns_original_tour_when_no_candidate_improves():
    matrix = _matrix_with_cheap_cycle([0, 1, 2, 3, 4, 5])
    initial_tour = [0, 1, 2, 3, 4, 5]

    result = improve_tour_restricted_three_opt(
        matrix,
        initial_tour,
        cut_positions=[1, 3, 4],
        max_passes=1,
    )

    assert result.initial_length == 6
    assert result.length == 6
    assert result.tour == initial_tour
    assert result.moves_applied == 0


def test_restricted_three_opt_payload_records_comparison_and_gap():
    result = RestrictedThreeOptResult(
        algorithm=RESTRICTED_THREE_OPT_ALGORITHM,
        initial_length=10,
        length=8,
        tour=[0, 3, 1, 2, 4, 5],
        moves_applied=1,
        passes=1,
        candidate_cut_count=3,
        candidates_evaluated=7,
        metadata={"strategy": "restricted_three_opt"},
    )

    payload = restricted_three_opt_payload(
        result,
        input_file=Path("data/raw/matrices/M.txt"),
        source_artifact=Path("results/best/step6-lkh-best.json"),
        n=6,
        command="cmd",
        lower_bound=5,
    )

    assert payload["algorithm"] == RESTRICTED_THREE_OPT_ALGORITHM
    assert payload["initial_length"] == 10
    assert payload["length"] == 8
    assert payload["improvement"] == 2
    assert payload["lower_bound"] == 5
    assert payload["absolute_gap"] == 3
    assert payload["relative_gap"] == 3 / 8
    assert payload["candidate_cut_count"] == 3
    assert payload["candidates_evaluated"] == 7
    assert payload["source_artifact"] == "results/best/step6-lkh-best.json"
    assert "created_at" in payload


def _matrix_with_cheap_cycle(cycle: list[int]) -> list[list[int]]:
    n = len(cycle)
    matrix = [[10 for _ in range(n)] for _ in range(n)]
    for city in range(n):
        matrix[city][city] = 0
    for index, from_city in enumerate(cycle):
        to_city = cycle[(index + 1) % n]
        matrix[from_city][to_city] = 1
        matrix[to_city][from_city] = 1
    return matrix
