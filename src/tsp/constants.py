from __future__ import annotations

from pathlib import Path
from typing import Final

CHALLENGE_CITY_COUNT: Final[int] = 1114
LECTURE_SAMPLE_CITY_COUNT: Final[int] = 94

CHALLENGE_MATRIX_PATH: Final[Path] = Path("data/raw/matrices/M.txt")
LECTURE_SAMPLE_MATRIX_PATH: Final[Path] = Path("data/raw/matrices/tsp_matrix1.txt")

MATRIX_FORMAT_PLAIN_WITH_SIZE: Final[str] = "plain_with_size"
MATRIX_FORMAT_PYTHON_LITERAL: Final[str] = "python_literal"

PYTHON_MATRIX_ASSIGNMENT_PREFIX: Final[str] = "M="
PYTHON_MATRIX_LIST_PREFIX: Final[str] = "[["
