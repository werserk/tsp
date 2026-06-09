from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from src.io.exceptions import MatrixParseError
from src.io.validation import validate_matrix
from src.tsp.constants import (
    MATRIX_FORMAT_PLAIN_WITH_SIZE,
    MATRIX_FORMAT_PYTHON_LITERAL,
    PYTHON_MATRIX_ASSIGNMENT_PREFIX,
    PYTHON_MATRIX_LIST_PREFIX,
)
from src.tsp.types import Matrix

MatrixFormat = str


@dataclass(frozen=True)
class MatrixData:
    matrix: Matrix
    n: int
    source_path: Path
    format: MatrixFormat


def detect_matrix_format(text: str) -> MatrixFormat:
    """Detect a supported matrix file format from text content."""

    stripped = text.strip()
    if not stripped:
        raise MatrixParseError("matrix file is empty")
    if stripped.startswith(PYTHON_MATRIX_ASSIGNMENT_PREFIX) or stripped.startswith(
        PYTHON_MATRIX_LIST_PREFIX
    ):
        return MATRIX_FORMAT_PYTHON_LITERAL
    return MATRIX_FORMAT_PLAIN_WITH_SIZE


def load_matrix(path: str | Path, *, validate: bool = True) -> MatrixData:
    """Load a TSP distance matrix from a supported lecturer/project format."""

    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8")
    matrix_format = detect_matrix_format(text)
    matrix = _parse_matrix(text, matrix_format)

    if validate:
        validate_matrix(matrix)

    return MatrixData(
        matrix=matrix,
        n=len(matrix),
        source_path=source_path,
        format=matrix_format,
    )


def _parse_matrix(text: str, matrix_format: MatrixFormat) -> Matrix:
    parsers = {
        MATRIX_FORMAT_PLAIN_WITH_SIZE: _parse_plain_matrix_with_size,
        MATRIX_FORMAT_PYTHON_LITERAL: _parse_python_literal_matrix,
    }
    return parsers[matrix_format](text.strip())


def _parse_plain_matrix_with_size(text: str) -> Matrix:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    first = lines[0].split()
    if len(first) != 1 or not first[0].isdigit():
        raise MatrixParseError("plain matrix must start with a single non-negative declared size")

    declared_size = int(first[0])
    data_lines = lines[1:]
    if len(data_lines) != declared_size:
        raise MatrixParseError(
            f"declared size {declared_size} does not match row count {len(data_lines)}"
        )

    try:
        matrix = [[int(value) for value in line.split()] for line in data_lines]
    except ValueError as exc:
        raise MatrixParseError("plain matrix contains a non-integer value") from exc

    if any(len(row) != declared_size for row in matrix):
        raise MatrixParseError(f"declared size {declared_size} does not match row length")
    return matrix


def _parse_python_literal_matrix(text: str) -> Matrix:
    literal = (
        text[len(PYTHON_MATRIX_ASSIGNMENT_PREFIX) :].strip()
        if text.startswith(PYTHON_MATRIX_ASSIGNMENT_PREFIX)
        else text
    )
    try:
        value = ast.literal_eval(literal)
    except (SyntaxError, ValueError) as exc:
        raise MatrixParseError("python literal matrix cannot be parsed") from exc

    if not isinstance(value, list):
        raise MatrixParseError("python literal matrix must be a list of rows")

    try:
        return [[int(item) for item in row] for row in value]
    except TypeError as exc:
        raise MatrixParseError("python literal matrix must contain row lists") from exc
    except ValueError as exc:
        raise MatrixParseError("python literal matrix contains a non-integer value") from exc
