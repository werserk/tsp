# Step 13 — Held-Karp slow-decay lower bound

Дата: 2026-06-10

## Objective

Улучшить verified lower bound для `data/raw/matrices/M.txt` строго выше текущего Step 9 bound:

```txt
previous_lower_bound: 65493.4373688764
upper_bound: 73934
success: new_lower_bound > 65493.4373688764 and <= 73934
```

## Sources and method choice

Рассмотренные источники/артефакты:

- `notes/11-step9-held-karp-one-tree.md` — уже реализован корректный Lagrangian 1-tree bound, но Step 9 остановился на 120 итерациях и best был на последней итерации.
- `docs/playbooks/tsp-lower-bound-improvement.md` — Track A ставит в приоритет усиление Held-Karp / Lagrangian 1-tree ascent через step-size schedules и parameter portfolios.
- Concorde README, University of Waterloo: Concorde is a branch-and-cut TSP code; cutting-plane route is strong but integration/build/certification cost is higher than immediate improvement of existing Held-Karp code.
- GWU TSP overview notes Held-Karp lower bound as a standard lower-bound technique for TSP.

Candidate ranking:

1. **Extend Step 9 ascent with slower decay** — high validity, very low implementation risk, direct continuity from current best. Selected.
2. Subtour LP / cutting plane — likely strong, but requires LP backend/separation integration and more certification work.
3. External Concorde/SCIP route — useful reference track, but no local solver was installed and build/integration is slower than Track A.

## Validity / proof sketch

For any penalty vector `π`, define adjusted costs:

```txt
c'(i,j) = c(i,j) + π_i + π_j
```

Every Hamiltonian cycle has degree `2` at every node, so for any tour `H`:

```txt
weight_c'(H) = weight_c(H) + 2 * sum_i π_i
```

A minimum adjusted 1-tree is no more expensive than any Hamiltonian cycle under adjusted costs, because a Hamiltonian cycle is feasible for the 1-tree relaxation. Therefore:

```txt
min_1tree weight_c'(T) - 2 * sum_i π_i <= weight_c(H)
```

This holds for the optimal tour, so each iteration's value is a valid lower bound. Taking the maximum over 1000 iterations remains a valid lower bound. This argument does not require triangle inequality.

Precision policy: artifact stores the computed float64 lower bound. Since input distances are integers, `ceil(lower_bound)` is safe for an integer-friendly statement.

## Implementation or solver integration

New reproducible runner:

```txt
experiments/step13_held_karp_decay_099.py
```

It reuses the existing independent 1-tree bound implementation, changes only the subgradient schedule, and writes a new best artifact only after assertions pass:

```txt
root_city: 0
iterations: 1000
initial_step_size: 64.0
step_decay: 0.99
```

Why this schedule: Step 9 used `step_decay=0.96`; exploratory bounded runs showed slower decay continues improving the lower bound after iteration 120.

## Experiment command

```bash
PYTHONUNBUFFERED=1 python experiments/step13_held_karp_decay_099.py 2>&1 | tee results/runs/step13-held-karp-decay-099.log
```

Runtime:

```txt
runtime_seconds: 387.290
best_iteration: 999
iterations_run: 1000
```

## Verification

Independent verifier evidence:

```bash
python -m pytest tests/test_step9_held_karp_one_tree.py tests/test_step13_held_karp_decay_099.py
```

Result:

```txt
6 passed
```

The Step 13 test reloads the saved `best_penalties`, recomputes the adjusted 1-tree lower bound from `data/raw/matrices/M.txt`, and checks:

```txt
recomputed_lower_bound == artifact lower_bound within 1e-7
lower_bound > previous best
lower_bound <= current upper bound
artifact gap fields match formulas
```

## Result

New verified lower bound:

```txt
lower_bound: 72711.81768955325
integer_lower_bound: 72712
upper_bound: 73934
```

Improvement over Step 9:

```txt
+7218.38032067685
```

Artifact:

```txt
results/best/step13-held-karp-decay-099-lower-bound.json
```

Log:

```txt
results/runs/step13-held-karp-decay-099.log
```

## Gap update

```txt
72711.81768955325 <= OPT <= 73934
integer interval: 72712 <= OPT <= 73934
absolute_gap: 1222.1823104467476
relative_gap_to_lower: 1.680857870538894%
relative_gap_to_upper: 1.6530720784033701%
```

Previous relative gap to lower was `12.887646411936071%`; the new lower-bound gap is `1.680857870538894%`.

## Decision

Status: accepted
Type: lower_bound
Candidate value: `72711.81768955325`
Current best before Step 13: `65493.4373688764`
Strict improvement: yes
Verification: passed
Decision: promote
Reason: valid Lagrangian 1-tree lower bound; independently recomputed from saved penalties; below current upper bound.

## Next candidate

If more time is available, continue Track A with a bounded schedule portfolio around `step_decay=0.99..0.995`, or move to Track B subtour LP/cutting-plane for an independent lower-bound family.
