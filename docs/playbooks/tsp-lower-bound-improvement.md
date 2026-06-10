# TSP Lower-Bound Improvement Playbook

## Objective

Improve the verified lower bound for the 1114-city TSP challenge instance.

This playbook is not a research-only checklist. Research is required, but the delivery goal is a new mathematically valid lower bound.

## Current baseline

```txt
challenge_input: data/raw/matrices/M.txt
cities: 1114
current_lower_bound: 65493.4373688764
current_lower_artifact: results/best/step9-held-karp-one-tree.json
current_upper_bound: 73934
current_upper_artifact: results/best/step6-lkh-best.json
current_interval: 65493.4373688764 <= OPT <= 73934
absolute_gap: 8440.562631123597
relative_gap_to_lower: 12.887646411936071%
relative_gap_to_upper: 11.416347865831144%
```

A new lower-bound result is successful only if:

```txt
new_lower_bound > 65493.4373688764
new_lower_bound <= 73934
```

## Compute policy

Approved mode: **aggressive local**.

Allowed:

- local solver builds;
- web research over papers, solver docs, GitHub, and benchmark writeups;
- multi-hour local runs;
- external open-source solvers if their output is independently verified.

Not approved by default:

- runs expected to take days;
- paid cloud/GPU/remote compute;
- destructive system-wide installs;
- publishing or submitting results externally.

Ask Maxim before crossing those boundaries.

## Required cycle

Use the `research-to-experiment-cycle` skill.

Each serious lower-bound attempt must produce:

1. research note or source summary;
2. method selection rationale;
3. proof/validity sketch for why the value is a lower bound;
4. implementation or solver-integration plan;
5. tests or independent checks on small instances;
6. bounded run artifact;
7. independent verification;
8. promote/reject decision.

Do not promote a result solely because a solver printed a number.

## Priority tracks

### Track A — strengthen Held-Karp / Lagrangian 1-tree ascent

Reason: this extends the current best lower-bound method and may produce an owned, explainable improvement.

Research and experiment with:

- subgradient step-size schedules;
- multiple multiplier starts;
- root selection and several-root ascent;
- stabilized/volume-like updates;
- candidate-edge restriction vs full graph;
- stronger stopping criteria and plateau escape;
- reproducible parameter portfolios.

Acceptance requirement:

- proof note that each 1-tree relaxation value is a valid lower bound;
- independent recomputation of the best bound from saved multipliers/tree data or a deterministic verifier;
- artifact with parameters, iterations, runtime, seed, and final multipliers summary.

### Track B — subtour LP / cutting-plane lower bound

Reason: SOTA TSP lower bounds are typically polyhedral/cutting-plane based.

Research and experiment with:

- Dantzig-Fulkerson-Johnson subtour relaxation;
- subtour separation;
- comb/blossom/cut families if feasible;
- LP backends such as HiGHS, SCIP, QSopt, or other accessible open-source tools;
- Concorde as a reference branch-and-cut implementation.

Acceptance requirement:

- proof note that the relaxation value is a lower bound for the symmetric TSP instance;
- exact mapping from `M.txt` to solver input;
- solver logs/configs preserved under `results/runs/`;
- parsed lower-bound/certificate metadata saved in JSON.

### Track C — external reference solvers

Reason: external solvers can reveal the achievable lower-bound scale and prevent wasting time on weak tracks.

Candidates:

- Concorde TSP Solver;
- SCIP examples/plugins where applicable;
- reputable TSP/cutting-plane repositories;
- academic code accompanying papers.

Acceptance requirement:

- build and run are reproducible locally;
- input conversion is documented;
- output bound is independently checked or at least audited against solver documentation;
- if the solver gives a full optimum/certificate, record both lower and upper information separately.

### Track D — assignment / matching / MST-derived relaxations

Reason: useful as quick baselines and sanity checks, but less likely to beat Held-Karp alone.

Use only if research shows a concrete strengthening route, for example:

- assignment relaxation with subtour elimination additions;
- minimum 2-matching relaxation;
- one-tree variants feeding Held-Karp starts.

## Result artifact policy

Only strict improvements go under `results/best/`.

Recommended new-best path:

```txt
results/best/step13-<method>-lower-bound.json
```

Non-improvements and partial runs go under:

```txt
results/runs/
```

Every best lower-bound artifact must include:

```json
{
  "type": "lower_bound",
  "algorithm": "...",
  "lower_bound": 0.0,
  "previous_lower_bound": 65493.4373688764,
  "upper_bound": 73934,
  "absolute_gap": 0.0,
  "relative_gap_to_lower": 0.0,
  "input_matrix": "data/raw/matrices/M.txt",
  "proof_sketch": "...",
  "verification": "...",
  "command": "...",
  "parameters": {},
  "runtime_seconds": 0.0,
  "created_at": "..."
}
```

## Verification rules

Before claiming a new lower bound:

1. Verify `lower_bound <= 73934`.
2. Verify the method applies to the exact TSP variant represented by `M.txt`.
3. Recompute or audit the bound using code independent from the producing routine when feasible.
4. Run focused tests on tiny instances where the lower-bound behavior is known.
5. Update the gap using the current upper bound.

## Stop conditions for a `/goal` run

Stop only when one is true:

1. verified lower bound improves above `65493.4373688764`;
2. three serious lower-bound tracks are exhausted with evidence;
3. the next run would exceed aggressive-local budget;
4. external install/compute requires explicit user approval;
5. the approach is discovered to be invalid for this problem variant.

## Reporting format

Use this result note structure:

```md
# Step XX — <method> lower bound

## Objective
## Sources and method choice
## Validity / proof sketch
## Implementation or solver integration
## Experiment command
## Verification
## Result
## Gap update
## Decision
## Next candidate
```
