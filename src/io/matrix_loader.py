from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .validation import validate_matrix


Matrix = list[list[int]]


@dataclass(frozen=True)
class MatrixData:
    matrix: Matrix
    n: int
    source_path: Path
    format: str


def load_matrix(path: str | Path, *, validate: bool = True) -> MatrixData:
    """Load a TSP distance matrix from a supported lecturer/project format."""

    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"matrix file is empty: {source_path}")

    if text.startswith("M=") or text.startswith("[["):
        matrix = _parse_python_literal_matrix(text)
        matrix_format = "python_literal"
    else:
        matrix = _parse_plain_matrix_with_size(text)
        matrix_format = "plain_with_size"

    if validate:
        validate_matrix(matrix)

    return MatrixData(
        matrix=matrix,
        n=len(matrix),
        source_path=source_path,
        format=matrix_format,
    )


def _parse_plain_matrix_with_size(text: str) -> Matrix:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    first = lines[0].split()
    if len(first) != 1 or not first[0].isdigit():
        raise ValueError("plain matrix must start with a single non-negative declared size")

    declared_size = int(first[0])
    data_lines = lines[1:]
    if len(data_lines) != declared_size:
        raise ValueError(
            f"declared size {declared_size} does not match row count {len(data_lines)}"
        )

    matrix = [[int(value) for value in line.split()] for line in data_lines]
    if any(len(row) != declared_size for row in matrix):
        raise ValueError(f"declared size {declared_size} does not match row length")
    return matrix


def _parse_python_literal_matrix(text: str) -> Matrix:
    literal = text[2:].strip() if text.startswith("M=") else text
    value = ast.literal_eval(literal)
    if not isinstance(value, list):
        raise ValueError("python literal matrix must be a list of rows")
    return [[int(item) for item in row] for row in value]
