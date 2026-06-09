#!/usr/bin/env python3
"""Step 6 prerequisite: export the challenge matrix to TSPLIB FULL_MATRIX."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io.matrix_loader import load_matrix
from src.io.tsplib import write_explicit_tsplib
from src.tsp.constants import CHALLENGE_MATRIX_PATH

OUTPUT_PATH = Path("data/processed/challenge-full-matrix.tsp")
TSPLIB_NAME = "tsp_1114_challenge"


def main() -> None:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    output_path = ROOT / OUTPUT_PATH
    write_explicit_tsplib(data.matrix, output_path, name=TSPLIB_NAME)
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
