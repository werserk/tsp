# Step 14 — Concorde linkern upper-bound negative result

## Objective

Find a valid tour with verified length `< 73934` using a local Concorde `linkern` build on the explicit 1114×1114 matrix.

## Sources considered

- Concorde 03.12.19 source release: local `linkern` heuristic supports TSPLIB `EDGE_WEIGHT_TYPE: EXPLICIT` / matrix norm and writes cycle artifacts.
- Project incumbent: LKH tour length `73934` in `results/best/step6-lkh-best.json`.
- Step 13 targeted LKH: no strict improvement over `73934`.

## Build / integration

Local-only build under `tools/`:

```txt
tools/co031219.tgz
tools/concorde-src/concorde/
tools/concorde-build/LINKERN/linkern
```

Build note: patched Concorde's old `h->h_addr` usage to `h->h_addr_list[0]` for current Linux headers.

Download SHA-256:

```txt
c3650a59c8d57e0a00e81c1288b994a99c5aa03e5d96a314834c2d8f9505c724
```

## Validity contract

A `linkern` result is accepted only after:

1. parse Concorde node-cycle or edge-list cycle output;
2. verify exactly 1114 cities;
3. verify each city appears once;
4. recompute closed-tour length from `data/raw/matrices/M.txt` with `tour_length(..., validate=True)`;
5. compare recomputed length to solver-reported `Overall Best Cycle` when present;
6. promote only if verified length `< 73934`.

## Experiment

Command:

```bash
PYTHONUNBUFFERED=1 python experiments/step14_concorde_linkern.py --configs from_lkh_q3,from_lkh_a20,from_lkh_a50,random_q3,random_a20 --seeds 1-50 --job-timeout-seconds 90 --time-bound-seconds 60 --run-kicks 1114 --resume 2>&1 | tee results/runs/step14-linkern-wave.log
```

Configs:

```txt
from_lkh_q3: start from incumbent LKH tour, default sparse set
from_lkh_a20: start from incumbent LKH tour, 20-nearest sparse set
from_lkh_a50: start from incumbent LKH tour, 50-nearest sparse set
random_q3: generated start, default sparse set
random_a20: generated start, 20-nearest sparse set
```

## Verification

Independent recheck completed for every finished record.

```txt
jobs_completed: 250
best_verified_length: 73934
length_distribution: {'73934': 151, '73947': 1, '73949': 1, '73953': 1, '73956': 1, '73957': 1, '73958': 1, '73960': 1, '73962': 1, '73963': 1, '73964': 3, '73968': 1, '73969': 1, '73970': 1, '73973': 1, '73974': 1, '73977': 3, '73978': 1, '73979': 1, '73980': 4, '73984': 2, '73985': 1, '73988': 1, '73989': 1, '73990': 1, '73991': 1, '73993': 1, '73994': 3, '73996': 1, '73998': 2, '73999': 1, '74002': 1, '74004': 1, '74006': 3, '74007': 1, '74008': 1, '74013': 1, '74014': 1, '74015': 2, '74019': 1, '74020': 1, '74022': 1, '74023': 1, '74025': 1, '74028': 1, '74030': 1, '74031': 2, '74032': 1, '74037': 2, '74039': 2, '74042': 1, '74043': 2, '74044': 1, '74045': 1, '74046': 1, '74048': 1, '74051': 1, '74053': 2, '74055': 1, '74066': 1, '74071': 2, '74072': 2, '74074': 2, '74084': 1, '74094': 1, '74097': 1, '74100': 1, '74106': 1, '74107': 1, '74111': 1, '74113': 1, '74114': 1, '74119': 1, '74127': 1, '74132': 1, '74197': 1, '74235': 1, '74286': 1}
by_config:
    from_lkh_a20: jobs=50, best=73934
  from_lkh_a50: jobs=50, best=73934
  from_lkh_q3: jobs=50, best=73934
  random_a20: jobs=50, best=73934
  random_q3: jobs=50, best=73953
strict_improvement: false
```

## Result

No promoted upper-bound improvement.

```txt
current_upper_bound: 73934
best_step14_length: 73934
improvement: 0
```

Artifacts:

```txt
results/runs/step14-linkern-summary.json
results/runs/step14-linkern-wave.json
results/runs/step14-linkern-progress.jsonl
results/runs/step14-linkern-wave.log
experiments/step14_concorde_linkern.py
```

## Gap update

No `results/best/` upper-bound artifact was written. Current interval remains:

```txt
65493.4373688764 <= OPT <= 73934
relative_gap_to_lower: 12.887646411936%
```

## Decision

Rejected for promotion. Concorde `linkern` is a valid local verifier-backed candidate, but in this wave it only tied the incumbent when starting from the LKH tour and produced worse tours from generated starts.

## Next candidate

Wait for the active Step 12 `D_trials5000_r3` LKH wave to finish its budget. If it also fails to improve, the remaining high-impact upper-bound route is adapting GA-EAX to explicit full-matrix distances or running a longer LKH candidate-set/initial-tour portfolio.
