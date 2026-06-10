# Step 13 — targeted LKH upper-bound negative result

## Objective

Find a valid tour with verified length `< 73934` using LKH configurations not covered by the completed Step 12 jobs.

## Sources and method choice

- LKH 2.0.11 documentation: Lin-Kernighan-Helsgaun remains the strongest local solver already integrated in the project; relevant knobs include `PATCHING_A`, `PATCHING_C`, `MOVE_TYPE`, `BACKTRACKING`, and `GAIN_CRITERION`.
- Concorde documentation: exact symmetric TSP reference solver, but no local binary is present in this workspace.
- GA-EAX repository: Edge Assembly Crossover is a strong TSP heuristic, but the available code expects coordinate TSPLIB input and does not natively accept this challenge's explicit full matrix.
- Project prior artifacts: restricted 3-opt, LKH `RUNS=1` multi-seed, and Step 12 A/B/C portfolio did not beat `73934`.

Candidate selected: targeted LKH configs with separate artifacts so the ongoing Step 12 ledger is not overwritten.

## Feasibility / tour-validity contract

A candidate tour is valid only if:

1. `parse_tsplib_tour` returns exactly 1114 cities;
2. `validate_tour(tour, 1114)` passes;
3. `tour_length(matrix, tour, validate=True)` recomputes the solver length from `data/raw/matrices/M.txt`;
4. verified length is strictly below `73934` before promotion.

## Implementation or solver integration

Added `experiments/step13_lkh_targeted_wave.py`:

- uses existing `write_explicit_tsplib`, `parse_tsplib_tour`, `validate_tour`, and `tour_length`;
- writes separate Step 13 parameter/tour files under `data/processed/`;
- writes progress to `results/runs/step13-lkh-targeted-progress.jsonl`;
- writes the run summary to `results/runs/step13-lkh-targeted-wave.json`;
- writes `results/best/step13-lkh-targeted-upper-bound.json` only on strict improvement.

## Experiment command

```bash
PYTHONUNBUFFERED=1 python experiments/step13_lkh_targeted_wave.py --configs E_patch_r3,F_move5_r3,G_backtracking_r3,H_gain_no_r3 --seeds 1-5 --job-timeout-minutes 20 --resume 2>&1 | tee results/runs/step13-lkh-targeted-wave.log
```

The run was stopped after 16 completed jobs because no configuration beat the current best and `H_gain_no_r3` was slower while producing `73941` on its first completed seed.

## Verification

Each completed job used:

```txt
parse_tsplib_tour + validate_tour + tour_length(matrix, tour, validate=True)
```

Summary:

```txt
jobs_completed: 16
best_verified_length: 73934
length_distribution: {'73934': 12, '73941': 3, '73947': 1}
strict_improvement: false
```

## Result

No strict upper-bound improvement.

```txt
current_upper_bound: 73934
best_step13_length: 73934
improvement: 0
```

Artifacts:

```txt
results/runs/step13-lkh-targeted-wave.json
results/runs/step13-lkh-targeted-progress.jsonl
results/runs/step13-lkh-targeted-wave.log
```

## Gap update

No promoted result; current interval remains:

```txt
65493.4373688764 <= OPT <= 73934
relative_gap_to_lower: 12.887646411936%
```

## Decision

Rejected for promotion. Keep artifacts under `results/runs/`.

## Next candidate

Let the ongoing Step 12 `D_trials5000_r3` bounded wave finish or stop at its time budget. If it also ties `73934`, the next stronger upper-bound candidate is either adapting GA-EAX to explicit full-matrix TSPLIB or obtaining a local Concorde/linkern build, both with independent verifier parsing before promotion.
