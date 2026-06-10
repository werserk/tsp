# Step 14 — Concorde no-branch cutting-plane lower bound

Дата: 2026-06-10

## Objective

Получить новый verified lower bound для challenge instance через независимый Concorde `-B` no-branch/cutting-plane route.

Baseline before this run:

```txt
input: data/raw/matrices/M.txt
n: 1114
previous_lower_bound: 72711.81768955325
upper_bound: 73934
success: parsed_lb > 72711.81768955325 and parsed_lb <= 73934
```

## Integration

Used local Concorde binary:

```txt
tools/concorde-bin/concorde
```

Binary source:

```txt
https://www.math.uwaterloo.ca/tsp/concorde/downloads/codes/linux24/concorde.gz
```

Smoke result:

```txt
Usage: ./concorde [-see below-] [dat_file]
-B do not branch
-I just solve the subtour polytope
-X write last root fractional solution
```

No source build was needed.

## Input mapping

Exported project matrix to TSPLIB explicit full matrix:

```txt
source: data/raw/matrices/M.txt
export: data/processed/M-full-matrix.tsp
format: TSPLIB_EXPLICIT_FULL_MATRIX
DIMENSION: 1114
EDGE_WEIGHT_TYPE: EXPLICIT
EDGE_WEIGHT_FORMAT: FULL_MATRIX
```

Independent mapping check:

```txt
entries_checked: 1240996
matches_source_matrix: true
```

This verifies that the TSPLIB file did not distort the `1114 × 1114` integer distance matrix.

## Command

```bash
cd /home/werserk/3-education/hse/combinatorial-optimization/tsp
PYTHONUNBUFFERED=1 python experiments/step14_concorde_no_branch.py \
  --concorde tools/concorde-bin/concorde \
  --seed 10
```

The script ran Concorde as:

```bash
tools/concorde-bin/concorde \
  -B \
  -s 10 \
  -u 73934 \
  -n results/runs/step14-concorde-root-problem \
  -X results/runs/step14-concorde-root.x \
  -o results/runs/step14-concorde-tour.out \
  data/processed/M-full-matrix.tsp
```

Run log:

```txt
results/runs/step14-concorde-root.log
```

Fractional root solution:

```txt
results/runs/step14-concorde-root.x
```

Concorde did not emit `results/runs/step14-concorde-tour.out` in this no-branch run, so there was no solver tour to verify.

## Parsed Concorde output

From `results/runs/step14-concorde-root.log`:

```txt
Final lower bound 73932.094971, upper bound 73934.000000
Exact lower bound: 73932.094971
Final LP has 1657 rows, 3011 columns, 22234 nonzeros
```

Parsing policy:

```txt
lower_bound_candidate = max(Final lower bound, Exact lower bound if present)
```

Parsed candidate:

```txt
lower_bound: 73932.094971
```

## Validity argument

Concorde with `-B` performs root LP/cutting-plane processing and stops without branching. The reported lower bound is the value of a linear relaxation/cutting-plane relaxation of the symmetric TSP polytope for the exported TSPLIB instance.

Because every Hamiltonian tour is feasible for the relaxation projection, the relaxation optimum is a valid lower bound for the original TSP optimum, assuming the matrix mapping is correct. The mapping was independently checked entry-by-entry.

The value is parsed separately from upper-bound/tour fields; `upper bound 73934.000000` is not used as a lower bound.

## Verification

Automated checks:

```bash
pytest tests/test_step14_concorde_no_branch.py tests/test_step13_held_karp_decay_099.py -q
```

Result:

```txt
7 passed
```

Artifact verification fields:

```txt
mapping_verification.matches_source_matrix: true
review_gate.strict_improvement: true
review_gate.lower_bound_le_upper_bound: true
```

## Result

New verified lower bound:

```txt
lower_bound: 73932.094971
integer_lower_bound: 73933
upper_bound: 73934
```

Improvement over Step 13:

```txt
+1220.2772814467464
```

New interval:

```txt
73932.094971 <= OPT <= 73934
integer interval: 73933 <= OPT <= 73934
absolute_gap: 1.9050290000013774
relative_gap_to_lower: 0.002576728010681462%
relative_gap_to_upper: 0.002576661617119833%
```

Best artifact:

```txt
results/best/step14-concorde-no-branch-lower-bound.json
```

## Review gate decision

```txt
decision: promote
reason: parsed Concorde lower bound is a strict improvement and remains <= current upper bound.
```

## Next candidate

The interval is now extremely tight but not closed in integer terms:

```txt
73933 <= OPT <= 73934
```

Next useful routes:

1. Run full Concorde branch-and-cut with incumbent `-u 73934` to try proving `OPT = 73934` or finding/proving `73933`.
2. Independently inspect whether the known LKH tour of `73934` can be improved by `1` via a targeted exact/local search around the incumbent.
3. Do not spend more time on Held-Karp for LB unless Concorde exact proof is blocked; Concorde already reduced the gap to about `1.905`.
