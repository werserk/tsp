#!/usr/bin/env python3
"""Audit raw TSP matrix files for Step 1: understand the data."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_DIR = ROOT / "data" / "raw" / "matrices"
OUT = ROOT / "data" / "processed" / "step1-data-audit.json"


def parse_plain_matrix(path: Path) -> tuple[int | None, list[list[int]], str]:
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    first = lines[0].split()
    declared = int(first[0]) if len(first) == 1 and first[0].isdigit() else None
    data_lines = lines[1:] if declared is not None else lines
    rows = [[int(x) for x in line.split()] for line in data_lines]
    fmt = "plain: first line declares n, then n whitespace-separated integer rows"
    return declared, rows, fmt


def parse_python_literal_matrix(path: Path) -> tuple[int | None, list[list[int]], str]:
    text = path.read_text().strip()
    literal = text[2:] if text.startswith("M=") else text
    rows = [[int(x) for x in row] for row in ast.literal_eval(literal)]
    fmt = "python literal assignment: M=[[...], [...], ...]"
    return None, rows, fmt


def audit_matrix(path: Path, declared: int | None, rows: list[list[int]], fmt: str) -> dict:
    n_rows = len(rows)
    row_lengths = [len(row) for row in rows]
    unique_lengths = sorted(set(row_lengths))
    n_cols = unique_lengths[0] if len(unique_lengths) == 1 else None
    square = n_rows == n_cols

    negative_count = 0
    zero_offdiag_count = 0
    nonzero_diagonal_examples = []
    global_min = global_max = None
    offdiag_min = offdiag_max = None
    offdiag_sum = 0
    offdiag_count = 0
    smallest = []
    largest = []

    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            global_min = value if global_min is None else min(global_min, value)
            global_max = value if global_max is None else max(global_max, value)
            if value < 0:
                negative_count += 1
            if i == j:
                if value != 0 and len(nonzero_diagonal_examples) < 10:
                    nonzero_diagonal_examples.append([i, value])
                continue
            if value == 0:
                zero_offdiag_count += 1
            offdiag_min = value if offdiag_min is None else min(offdiag_min, value)
            offdiag_max = value if offdiag_max is None else max(offdiag_max, value)
            offdiag_sum += value
            offdiag_count += 1
            smallest.append((value, i, j))
            largest.append((value, i, j))
            if len(smallest) > 20:
                smallest = sorted(smallest)[:10]
            if len(largest) > 20:
                largest = sorted(largest, reverse=True)[:10]

    asymmetric_pair_count = 0
    asymmetry_max_abs_difference = 0
    asymmetry_examples = []
    if square:
        for i in range(n_rows):
            for j in range(i + 1, n_rows):
                diff = rows[i][j] - rows[j][i]
                if diff:
                    asymmetric_pair_count += 1
                    asymmetry_max_abs_difference = max(asymmetry_max_abs_difference, abs(diff))
                    if len(asymmetry_examples) < 10:
                        asymmetry_examples.append([i, j, rows[i][j], rows[j][i], diff])

    triangle_violations = []
    probes = list(range(n_rows)) if n_rows <= 150 else sorted(set(list(range(30)) + [n_rows // 2, n_rows - 1]))
    if square:
        for i in probes:
            for j in probes:
                direct = rows[i][j]
                for k in probes:
                    if direct > rows[i][k] + rows[k][j]:
                        triangle_violations.append([i, j, k, direct, rows[i][k], rows[k][j]])
                        if len(triangle_violations) >= 10:
                            break
                if len(triangle_violations) >= 10:
                    break
            if len(triangle_violations) >= 10:
                break

    return {
        "file": path.name,
        "format": fmt,
        "file_size_bytes": path.stat().st_size,
        "declared_size": declared,
        "rows": n_rows,
        "unique_row_lengths": unique_lengths,
        "columns_if_uniform": n_cols,
        "square": square,
        "matches_declared_size": declared is None or declared == n_rows == n_cols,
        "diagonal_all_zero": square and not nonzero_diagonal_examples,
        "nonzero_diagonal_examples": nonzero_diagonal_examples,
        "negative_count": negative_count,
        "zero_offdiag_count": zero_offdiag_count,
        "symmetric": square and asymmetric_pair_count == 0,
        "asymmetric_pair_count": asymmetric_pair_count,
        "asymmetry_max_abs_difference": asymmetry_max_abs_difference,
        "asymmetry_examples": asymmetry_examples,
        "global_min": global_min,
        "global_max": global_max,
        "offdiag_min": offdiag_min,
        "offdiag_max": offdiag_max,
        "offdiag_mean": offdiag_sum / offdiag_count if offdiag_count else None,
        "smallest_directed_edges_sample": sorted(smallest)[:10],
        "largest_directed_edges_sample": sorted(largest, reverse=True)[:10],
        "triangle_inequality_violation_examples": triangle_violations,
    }


def main() -> None:
    inputs = [MATRIX_DIR / "M.txt", MATRIX_DIR / "tsp_matrix1.txt"]
    reports = []
    for path in inputs:
        if path.name == "M.txt":
            declared, rows, fmt = parse_plain_matrix(path)
        else:
            declared, rows, fmt = parse_python_literal_matrix(path)
        reports.append(audit_matrix(path, declared, rows, fmt))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
