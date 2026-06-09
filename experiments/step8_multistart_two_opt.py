#!/usr/bin/env python3
"""Step 8: run own multi-start nearest-neighbor + 2-opt upper-bound benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.heuristics.multistart_two_opt import (
    multistart_nearest_neighbor_two_opt,
    rank_starts_by_nearest_neighbor_length,
    save_multistart_two_opt_result,
)
from src.io.matrix_loader import load_matrix
from src.io.validation import validate_tour
from src.tsp.constants import CHALLENGE_MATRIX_PATH
from src.tsp.tour import tour_length

DEFAULT_UPPER_ARTIFACT = Path("results/best/step6-lkh-best.json")
DEFAULT_LOWER_ARTIFACT = Path("results/best/step7-several-root-one-tree.json")
DEFAULT_OUTPUT_PATH = Path("results/best/step8-multistart-two-opt.json")
DEFAULT_START_STRIDE = 16


def main() -> None:
    args = _parse_args()
    matrix_path = ROOT / CHALLENGE_MATRIX_PATH
    upper_artifact_path = ROOT / args.current_best_upper_artifact
    lower_artifact_path = ROOT / args.lower_bound_artifact

    data = load_matrix(matrix_path)
    candidate_starts = _candidate_starts(data.n, stride=args.start_stride, include_last=True)
    if args.top_ranked_starts is None:
        starts = candidate_starts
    else:
        ranked_starts = rank_starts_by_nearest_neighbor_length(
            data.matrix,
            candidate_starts,
            limit=args.top_ranked_starts,
        )
        starts = [candidate.start_city for candidate in ranked_starts]
    if args.max_starts is not None:
        starts = starts[: args.max_starts]

    upper_artifact = json.loads(upper_artifact_path.read_text(encoding="utf-8"))
    lower_artifact = json.loads(lower_artifact_path.read_text(encoding="utf-8"))
    current_best_upper_bound = int(upper_artifact["length"])
    lower_bound = int(lower_artifact["lower_bound"])

    result = multistart_nearest_neighbor_two_opt(data.matrix, starts)
    result = replace(
        result,
        metadata={
            **result.metadata,
            "candidate_start_stride": args.start_stride,
            "candidate_start_count": len(candidate_starts),
            "top_ranked_starts": args.top_ranked_starts,
            "evaluated_starts": starts,
        },
    )
    validate_tour(result.tour, data.n)
    independently_checked_length = tour_length(data.matrix, result.tour, validate=True)
    if independently_checked_length != result.length:
        raise AssertionError(
            "independent tour length check mismatch: "
            f"{independently_checked_length} != {result.length}"
        )

    command = _command_string(args)
    save_multistart_two_opt_result(
        result,
        output_path=ROOT / args.output_path,
        input_file=CHALLENGE_MATRIX_PATH,
        n=data.n,
        command=command,
        current_best_upper_bound=current_best_upper_bound,
        lower_bound=lower_bound,
    )

    print(f"algorithm={result.algorithm}")
    print(f"input={CHALLENGE_MATRIX_PATH}")
    print(f"n={data.n}")
    print(f"start_stride={args.start_stride}")
    print(f"candidate_starts={len(candidate_starts)}")
    print(f"top_ranked_starts={args.top_ranked_starts}")
    print(f"starts_checked={result.starts_checked}")
    print(f"best_start_city={result.best_start_city}")
    print(f"best_initial_length={result.best_initial_length}")
    print(f"best_length={result.length}")
    print(f"previous_upper_bound={current_best_upper_bound}")
    print(f"improvement_over_previous_upper_bound={current_best_upper_bound - result.length}")
    print(f"lower_bound={lower_bound}")
    print(f"absolute_gap={result.length - lower_bound}")
    print(f"relative_gap={(result.length - lower_bound) / result.length:.6f}")
    print(f"total_two_opt_moves={result.total_two_opt_moves}")
    print(f"output={args.output_path}")


def _candidate_starts(n: int, *, stride: int, include_last: bool) -> list[int]:
    if stride <= 0:
        raise ValueError("start stride must be positive")
    starts = list(range(0, n, stride))
    if include_last and starts[-1] != n - 1:
        starts.append(n - 1)
    return starts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-stride", type=int, default=DEFAULT_START_STRIDE)
    parser.add_argument("--top-ranked-starts", type=int, default=None)
    parser.add_argument("--max-starts", type=int, default=None)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--current-best-upper-artifact", type=Path, default=DEFAULT_UPPER_ARTIFACT)
    parser.add_argument("--lower-bound-artifact", type=Path, default=DEFAULT_LOWER_ARTIFACT)
    return parser.parse_args()


def _command_string(args: argparse.Namespace) -> str:
    parts = ["python", "experiments/step8_multistart_two_opt.py"]
    if args.start_stride != DEFAULT_START_STRIDE:
        parts.extend(["--start-stride", str(args.start_stride)])
    if args.top_ranked_starts is not None:
        parts.extend(["--top-ranked-starts", str(args.top_ranked_starts)])
    if args.max_starts is not None:
        parts.extend(["--max-starts", str(args.max_starts)])
    if args.output_path != DEFAULT_OUTPUT_PATH:
        parts.extend(["--output-path", str(args.output_path)])
    return " ".join(parts)


if __name__ == "__main__":
    main()
