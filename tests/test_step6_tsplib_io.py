from __future__ import annotations

from pathlib import Path

from src.io.tsplib import parse_tsplib_tour, write_explicit_tsplib


def test_write_explicit_tsplib_uses_full_matrix_format(tmp_path: Path):
    matrix = [
        [0, 2, 9],
        [2, 0, 4],
        [9, 4, 0],
    ]
    output_path = tmp_path / "sample.tsp"

    write_explicit_tsplib(matrix, output_path, name="sample")

    assert output_path.read_text(encoding="utf-8") == (
        "NAME: sample\n"
        "TYPE: TSP\n"
        "COMMENT: Exported from project distance matrix\n"
        "DIMENSION: 3\n"
        "EDGE_WEIGHT_TYPE: EXPLICIT\n"
        "EDGE_WEIGHT_FORMAT: FULL_MATRIX\n"
        "EDGE_WEIGHT_SECTION\n"
        "0 2 9\n"
        "2 0 4\n"
        "9 4 0\n"
        "EOF\n"
    )


def test_parse_tsplib_tour_converts_one_based_city_indices_to_zero_based(tmp_path: Path):
    tour_path = tmp_path / "sample.tour"
    tour_path.write_text(
        "NAME : sample.tour\n"
        "TYPE : TOUR\n"
        "DIMENSION : 4\n"
        "TOUR_SECTION\n"
        "1\n"
        "4\n"
        "2\n"
        "3\n"
        "-1\n"
        "EOF\n",
        encoding="utf-8",
    )

    assert parse_tsplib_tour(tour_path) == [0, 3, 1, 2]


def test_parse_tsplib_tour_handles_multiple_indices_per_line(tmp_path: Path):
    tour_path = tmp_path / "sample.tour"
    tour_path.write_text("TOUR_SECTION\n1 3 2 -1\nEOF\n", encoding="utf-8")

    assert parse_tsplib_tour(tour_path) == [0, 2, 1]
