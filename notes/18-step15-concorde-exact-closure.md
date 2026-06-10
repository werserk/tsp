# Step 15 — Concorde exact closure attempt

Дата: 2026-06-10

## Objective

Close the final integer gap for the 1114-city `FULL_MATRIX` TSP instance:

```txt
A) verified tour length 73933 -> OPT = 73933
B) parsed LB > 73933 with UB 73934 -> OPT = 73934
C) Concorde explicitly proves optimality of 73934 -> OPT = 73934
```

Baseline before Step 15:

```txt
previous verified lower bound: 73932.094971
verified incumbent upper bound: 73934
previous lower artifact: results/best/step14-concorde-no-branch-lower-bound.json
incumbent upper artifact: results/best/step6-lkh-best.json
TSPLIB input: data/processed/M-full-matrix.tsp
```

## Prerequisite verification

TSPLIB export was checked before the run:

```txt
path: data/processed/M-full-matrix.tsp
size: 5760038 bytes
TYPE: TSP
DIMENSION: 1114
EDGE_WEIGHT_TYPE: EXPLICIT
EDGE_WEIGHT_FORMAT: FULL_MATRIX
EDGE_WEIGHT_SECTION present
EOF present
```

Concorde binary used:

```txt
tools/concorde-bin/concorde
```

The incumbent LKH tour was independently recomputed against the project matrix:

```txt
python - <<'PY'
import json
from pathlib import Path
from src.io.matrix_loader import load_matrix
from src.tsp.tour import tour_length
m = load_matrix(Path('data/raw/matrices/M.txt')).matrix
ub = json.loads(Path('results/best/step6-lkh-best.json').read_text())
print(tour_length(m, ub['tour'], validate=True))
PY
```

Result:

```txt
73934
```

## Command

Run from `results/runs/` so Concorde-generated files stay under `results/runs/`:

```bash
cd /home/werserk/3-education/hse/combinatorial-optimization/tsp/results/runs
PYTHONUNBUFFERED=1 timeout 4h ../../tools/concorde-bin/concorde \
  -u 73934 \
  -s 1 \
  -X step15-concorde-exact.x \
  -o step15-concorde-exact.tour \
  ../../data/processed/M-full-matrix.tsp \
  2>&1 | tee step15-concorde-exact.log
```

Metadata:

```txt
results/runs/step15-concorde-exact.meta
```

## Generated files

```txt
results/runs/step15-concorde-exact.log
results/runs/step15-concorde-exact.meta
results/runs/step15-concorde-exact.tour
results/runs/step15-concorde-exact.x
results/runs/step15-concorde-exact-summary.json
```

Parser:

```txt
experiments/step15_parse_concorde_exact.py
```

## Parsed log fields

From `results/runs/step15-concorde-exact.log`:

```txt
Final lower bound 73930.203925, upper bound 73934.000000
Exact lower bound: 73930.203925
Final LP has 1697 rows, 2282 columns, 26534 nonzeros
LOWER BOUND: 73930.203925   ACTIVE NODES: 1
LOWER BOUND: 73930.734375   ACTIVE NODES: 1
Optimal Solution: 73934.00
Number of bbnodes: 3
Total Running Time: 36.11 seconds
```

Parsed summary:

```txt
best_parsed_lower_bound: 73930.734375
best_parsed_upper_bound: 73934.0
explicit_optimality: true
bbnodes: 3
```

## Tour output verification

Concorde wrote:

```txt
results/runs/step15-concorde-exact.tour
```

Project verifier result:

```txt
city_count: 1114
verified_length: 74188
```

This file is **not** accepted as a 73934 or 73933 tour artifact. It is preserved as solver output only. The valid incumbent upper bound remains the independently verified LKH tour in:

```txt
results/best/step6-lkh-best.json
```

## Closure decision

Status: **closed**

Successful case:

```txt
C) Concorde explicitly proves optimality of 73934.
```

Reasoning:

1. The project already has a valid independently verified feasible tour of length `73934`.
2. Concorde was run as full branch-and-cut, not `-B`, with the valid incumbent `-u 73934`.
3. Concorde log explicitly reports:

```txt
Optimal Solution: 73934.00
Number of bbnodes: 3
```

Therefore:

```txt
OPT = 73934
```

## Final interval

```txt
73934 <= OPT <= 73934
OPT = 73934
```

## Notes / caveats

- The branch lower-bound values alone did not satisfy case B (`LB > 73933`); the closure comes from Concorde's explicit optimality proof, case C.
- The Concorde output tour file did not verify to `73934`; it must not replace the existing LKH upper-bound artifact.
- Step 14 best artifacts were not overwritten.
