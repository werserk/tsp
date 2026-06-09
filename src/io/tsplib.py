from __future__ import annotations

from pathlib import Path

from src.io.validation import validate_matrix
from src.tsp.types import Matrix, Tour

TSPLIB_COMMENT = "Exported from project distance matrix"
TSPLIB_TYPE = "TSP"
TSPLIB_EDGE_WEIGHT_TYPE = "EXPLICIT"
TSPLIB_EDGE_WEIGHT_FORMAT = "FULL_MATRIX"
TOUR_SECTION = "TOUR_SECTION"
EOF_MARKER = "EOF"
TOUR_END_MARKER = "-1"


def write_explicit_tsplib(matrix: Matrix, output_path: Path, *, name: str) -> None:
    """Write a symmetric explicit FULL_MATRIX TSPLIB file."""

    validate_matrix(matrix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        f"NAME: {name}",
        f"TYPE: {TSPLIB_TYPE}",
        f"COMMENT: {TSPLIB_COMMENT}",
        f"DIMENSION: {len(matrix)}",
        f"EDGE_WEIGHT_TYPE: {TSPLIB_EDGE_WEIGHT_TYPE}",
        f"EDGE_WEIGHT_FORMAT: {TSPLIB_EDGE_WEIGHT_FORMAT}",
        "EDGE_WEIGHT_SECTION",
    ]
    rows.extend(" ".join(str(value) for value in row) for row in matrix)
    rows.append(EOF_MARKER)
    output_path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def parse_tsplib_tour(tour_path: Path) -> Tour:
    """Parse a TSPLIB TOUR_SECTION into project zero-based city indices."""

    text = tour_path.read_text(encoding="utf-8")
    tokens = text.replace("\r", "\n").split()
    try:
        start_index = tokens.index(TOUR_SECTION) + 1
    except ValueError as exc:
        raise ValueError(f"TOUR_SECTION not found in {tour_path}") from exc

    tour: Tour = []
    for token in tokens[start_index:]:
        if token in {TOUR_END_MARKER, EOF_MARKER}:
            break
        tour.append(int(token) - 1)
    return tour
