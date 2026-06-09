from __future__ import annotations

from src.heuristics.multistart_two_opt import rank_starts_by_nearest_neighbor_length


MATRIX_WITH_DIFFERENT_NN_START_QUALITY = [
    [0, 15, 10, 10, 17],
    [15, 0, 7, 11, 20],
    [10, 7, 0, 2, 13],
    [10, 11, 2, 0, 13],
    [17, 20, 13, 13, 0],
]


def test_rank_starts_by_nearest_neighbor_length_orders_candidates_by_nn_length():
    ranked = rank_starts_by_nearest_neighbor_length(
        MATRIX_WITH_DIFFERENT_NN_START_QUALITY,
        starts=[0, 1, 2, 3, 4],
    )

    assert [item.start_city for item in ranked] == [3, 1, 0, 2, 4]
    assert [item.length for item in ranked] == [54, 56, 60, 60, 60]
    assert all(item.tour[0] == item.start_city for item in ranked)


def test_rank_starts_by_nearest_neighbor_length_can_limit_returned_candidates():
    ranked = rank_starts_by_nearest_neighbor_length(
        MATRIX_WITH_DIFFERENT_NN_START_QUALITY,
        starts=[0, 1, 2, 3, 4],
        limit=2,
    )

    assert len(ranked) == 2
    assert [item.start_city for item in ranked] == [3, 1]
