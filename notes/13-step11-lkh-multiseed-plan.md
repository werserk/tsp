# Step 11 — LKH multi-seed upper-bound search plan

> Goal: try to improve the current verified upper bound `73934` by running a systematic multi-seed LKH benchmark and preserving only verified best results.

## Current state

Current validated interval:

```txt
65493.437369 <= OPT <= 73934
```

Integer-friendly form:

```txt
65494 <= OPT <= 73934
```

Current best upper-bound artifact:

```txt
results/best/step6-lkh-best.json
```

Current best lower-bound artifact:

```txt
results/best/step9-held-karp-one-tree.json
```

## Verdict

Next priority: improve the upper bound with a systematic LKH multi-seed run.

Reason:

- LKH already gave the strongest upper-bound jump: `80585 -> 73934`.
- The previous LKH run was intentionally modest.
- The restricted 3-opt check did not improve the LKH tour.
- Multi-seed LKH is more likely to produce a useful improvement than writing another weak local-search heuristic.

Success criterion:

```txt
verified_length < 73934
```

## Step 1 — Confirm baseline

Verify the current best upper bound before running new experiments.

Command:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('results/best/step6-lkh-best.json')
data = json.loads(p.read_text())
print(data['length'])
assert data['length'] == 73934
PY
```

Also verify that the tour is independently checked through project code, not trusted from the solver output alone.

## Step 2 — Add multi-seed runner

Create:

```txt
experiments/step11_lkh_multiseed.py
```

The runner should:

- use canonical input:
  ```txt
  data/raw/matrices/M.txt
  ```
- reuse existing TSPLIB export / LKH integration code;
- accept a seed range/list;
- run LKH for each seed;
- independently verify each returned tour with project `tour_length(..., validate=True)`;
- collect per-seed metadata:
  - seed;
  - raw solver length;
  - verified project length;
  - runtime seconds;
  - LKH parameter file path;
  - LKH output tour path;
  - command / parameter summary;
- choose the minimum verified length.

Suggested CLI:

```bash
python experiments/step11_lkh_multiseed.py --seeds 1-20 --runs 1
```

## Step 3 — Add tests for result selection and artifact contracts

Create:

```txt
tests/test_step11_lkh_multiseed.py
```

Test only pure / cheap logic, not full LKH runtime.

Contracts to test:

1. Aggregation chooses the lowest verified length.
2. Artifact schema is stable.
3. A non-improving result is not marked as a new best.
4. A best candidate must contain verified project length.
5. The output path policy is respected:
   - if `best_verified_length < 73934` → `results/best/step11-lkh-multiseed-best.json`;
   - otherwise → `results/runs/step11-lkh-multiseed.json`.

## Step 4 — First run: cheap search

Run a bounded first wave:

```bash
python experiments/step11_lkh_multiseed.py --seeds 1-20 --runs 1
```

Purpose:

- estimate whether seeds produce variation;
- avoid wasting time on blind heavy tuning;
- get a reproducible artifact.

Expected output categories:

- best seed;
- best verified length;
- whether it improved `73934`;
- number of seeds completed;
- failures, if any.

## Step 5 — Output artifact policy

Use strict artifact routing.

If new verified upper bound is better:

```txt
results/best/step11-lkh-multiseed-best.json
```

If not better:

```txt
results/runs/step11-lkh-multiseed.json
```

Do not put non-best artifacts in `results/best/`.

## Step 6 — Verification

Run:

```bash
pytest -q
python experiments/step11_lkh_multiseed.py --seeds 1-20 --runs 1
python - <<'PY'
import json
from pathlib import Path
for p in [
    Path('results/best/step11-lkh-multiseed-best.json'),
    Path('results/runs/step11-lkh-multiseed.json'),
]:
    if p.exists():
        data = json.loads(p.read_text())
        print(p, data.get('best_verified_length') or data.get('length'))
PY
```

Before committing:

```bash
git diff --check
git status --short
```

## Step 7 — If first wave improves upper bound

Update:

```txt
README.md
AGENTS.md
notes/07-next-experiments-plan.md
```

Create result note:

```txt
notes/13-step11-lkh-multiseed.md
```

The note should include:

- seed range;
- LKH parameters;
- best seed;
- best verified length;
- previous upper bound `73934`;
- improvement amount;
- updated interval;
- independent verification statement.

## Step 8 — If first wave does not improve upper bound

Still create:

```txt
notes/13-step11-lkh-multiseed.md
```

But treat it as a neutral / negative benchmark result.

Do not update current bounds.

Recommended next run only if time allows:

```txt
seeds: 1..50 or 1..100
RUNS: 3-5
```

Possible LKH tuning parameters to explore after the cheap wave:

```txt
MAX_TRIALS
MOVE_TYPE
PATCHING_C
PATCHING_A
```

Avoid unlimited tuning. The result must remain explainable in a 15-minute oral defense.

## Step 9 — Commit

Use one thematic commit:

```bash
git add experiments/step11_lkh_multiseed.py \
        tests/test_step11_lkh_multiseed.py \
        notes/13-step11-lkh-multiseed.md \
        notes/13-step11-lkh-multiseed-plan.md \
        results/best/step11-lkh-multiseed-best.json \
        results/runs/step11-lkh-multiseed.json \
        README.md AGENTS.md notes/07-next-experiments-plan.md

git commit -m "Add LKH multiseed upper-bound search"
```

Adjust the `git add` list to include only files that actually exist and belong to Step 11.

## Decision rule after Step 11

If Step 11 improves the upper bound:

- make it the new current best;
- recompute the interval;
- prepare a concise explanation for the lecturer: LKH multi-seed + independent verifier.

If Step 11 does not improve the upper bound:

- keep `73934` as best upper bound;
- stop spending much time on self-written upper-bound local search;
- either run one heavier LKH tuning wave or return to Held-Karp lower-bound tuning.
