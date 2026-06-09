#!/usr/bin/env python3
"""Step 6: export the challenge instance to TSPLIB full-matrix format."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integrations.lkh import export_tsplib_full_matrix
from src.io.matrix_loader import load_matrix
from src.tsp.constants import CHALLENGE_MATRIX_PATH

TSPLIB_PATH = Path("data/processed/lkh/challenge-1114-full-matrix.tsp")


def main() -> None:
    data = load_matrix(ROOT / CHALLENGE_MATRIX_PATH)
    export_tsplib_full_matrix(
        data.matrix,
        output_path=ROOT / TSPLIB_PATH,
        name="challenge_1114_full_matrix",
    )
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"output={TSPLIB_PATH}")


if __name__ == "__main__":
    main()
