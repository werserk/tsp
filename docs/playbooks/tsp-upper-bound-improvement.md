# TSP Upper-Bound Improvement Playbook

## Objective

Improve the verified upper bound for the 1114-city TSP challenge instance by finding a shorter valid tour.

This playbook is not a “run heuristics randomly” checklist. Research is required, but the delivery goal is a new independently verified tour length.

## Current baseline

```txt
challenge_input: data/raw/matrices/M.txt
cities: 1114
current_upper_bound: 73934
current_upper_artifact: results/best/step6-lkh-best.json
current_lower_bound: 65493.4373688764
current_lower_artifact: results/best/step9-held-karp-one-tree.json
current_interval: 65493.4373688764 <= OPT <= 73934
absolute_gap: 8440.562631123597
relative_gap_to_lower: 12.887646411936071%
relative_gap_to_upper: 11.416347865831144%
```

A new upper-bound result is successful only if:

```txt
new_upper_bound < 73934
new_upper_bound >= 65493.4373688764
```

The second inequality is a consistency check against the current lower bound; a shorter tour below the lower bound means either the tour length or the lower bound is wrong.

## Compute policy

Approved mode: **aggressive local**.

Allowed:

- local solver builds;
- web research over papers, solver docs, GitHub, and benchmark writeups;
- multi-hour local runs;
- external open-source solvers if their tours are independently verified;
- parameter portfolios, multi-start searches, and resumable long runs.

Not approved by default:

- runs expected to take days;
- paid cloud/GPU/remote compute;
- destructive system-wide installs;
- publishing/submitting results externally.

Ask Maxim before crossing those boundaries.

## Required cycle

Use the `research-to-experiment-cycle` skill.

Each serious upper-bound attempt must produce:

1. research note or source summary;
2. method/config selection rationale;
3. feasibility note for the tour representation;
4. implementation or solver-integration plan;
5. tests or independent checks on small instances/parsers;
6. bounded run artifact;
7. independent tour verification with `tour_length(..., validate=True)` or equivalent;
8. promote/reject decision.

Do not promote a result solely because a solver printed a cost.

## Priority tracks

### Track A — stronger LKH portfolio

Reason: LKH produced the current best jump and still has configuration surface left.

Research and experiment with:

- broader seed/config portfolios;
- longer targeted runs only on configs that tie `73934` often;
- `MAX_TRIALS`, `RUNS`, `MOVE_TYPE`, `PATCHING_C`, `PATCHING_A`, `BACKTRACKING`, candidate-set options;
- restarts from existing best tour if supported and reproducible;
- resumable portfolio runner improvements if needed.

Acceptance requirement:

- every candidate tour is parsed and independently verified from `M.txt`;
- all non-improving runs remain in `results/runs/`;
- strict improvements only go to `results/best/`.

### Track B — alternative external solvers / metaheuristics

Reason: another mature solver may escape LKH's current local basin.

Candidates:

- Concorde as exact/branch-and-cut reference if it can produce tours/certificates locally;
- EAX genetic algorithm implementations;
- Lin-Kernighan variants;
- high-quality open TSP heuristic repositories with reproducible CLI output.

Acceptance requirement:

- local build/run documented;
- TSPLIB or matrix conversion audited;
- output tour parsed into project format;
- length verified independently.

### Track C — own post-optimization around current best tour

Reason: unlikely to beat LKH alone, but useful if targeted at specific weaknesses.

Research and experiment with:

- candidate-edge restricted 3-opt/4-opt/LK-like moves;
- don't-look bits and nearest-neighbor candidate lists;
- ejection-chain/k-opt neighborhoods if implementable;
- perturb-and-repair around current best tour;
- recombination/crossover between distinct near-best tours.

Acceptance requirement:

- tests on small instances for every move operator;
- no mutation of invalid tours;
- independent final verification;
- bounded runtime and negative result notes for non-improvements.

### Track D — hybrid UB/LB-informed search

Reason: lower-bound/cut/candidate information may suggest promising edges or pruning.

Use only if there is a concrete mechanism, for example:

- candidate sets from Held-Karp multipliers or 1-tree edges;
- edge frequency across near-best LKH tours;
- fixing/penalizing edges based on solver evidence;
- using lower-bound dual information to bias heuristic starts.

## Result artifact policy

Only strict improvements go under `results/best/`.

Recommended new-best path:

```txt
results/best/step13-<method>-upper-bound.json
```

Non-improvements and partial runs go under:

```txt
results/runs/
```

Every best upper-bound artifact must include:

```json
{
  "type": "upper_bound",
  "algorithm": "...",
  "length": 0,
  "previous_upper_bound": 73934,
  "lower_bound": 65493.4373688764,
  "absolute_gap": 0.0,
  "relative_gap_to_lower": 0.0,
  "relative_gap_to_upper": 0.0,
  "input_matrix": "data/raw/matrices/M.txt",
  "tour": [],
  "verification": "tour_length(..., validate=True)",
  "command": "...",
  "parameters": {},
  "seed": 1,
  "runtime_seconds": 0.0,
  "created_at": "..."
}
```

## Verification rules

Before claiming a new upper bound:

1. Verify the tour has exactly `1114` cities.
2. Verify every city appears exactly once.
3. Recompute tour length from `data/raw/matrices/M.txt` with validation enabled.
4. Verify recomputed length equals the artifact length.
5. Verify `length < 73934` for promotion.
6. Verify `length >= 65493.4373688764` for consistency with the lower bound.
7. Update the gap using the current lower bound.

## Parallel-run coordination with lower-bound goal

If a lower-bound improvement goal is running in parallel:

- do not mutate shared raw data or current best artifacts unless promoting a verified strict improvement;
- write intermediate logs under method-specific `results/runs/` names;
- before final gap calculation, reload both current best artifacts from disk;
- if both goals improve bounds, ensure the final interval remains valid.

## Stop conditions for a `/goal` run

Stop only when one is true:

1. verified upper bound improves below `73934`;
2. three serious upper-bound tracks are exhausted with evidence;
3. the next run would exceed aggressive-local budget;
4. external install/compute requires explicit user approval;
5. the approach is discovered to produce invalid or unverifiable tours.

## Reporting format

Use this result note structure:

```md
# Step XX — <method> upper bound

## Objective
## Sources and method choice
## Feasibility / tour-validity contract
## Implementation or solver integration
## Experiment command
## Verification
## Result
## Gap update
## Decision
## Next candidate
```
