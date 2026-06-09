# Step 12 — LKH portfolio runner with ETA/progress implementation plan

> Goal: implement option B — a bounded LKH tuning portfolio runner with predictable job count, ETA, resumable progress ledger, best-tour preservation, and final Markdown/HTML reports.

## Current context

Current verified interval:

```txt
65493.437369 <= OPT <= 73934
```

Current best upper-bound artifact:

```txt
results/best/step6-lkh-best.json
```

Current best lower-bound artifact:

```txt
results/best/step9-held-karp-one-tree.json
```

Previous upper-bound attempts:

- Step 10 restricted 3-opt on LKH tour: `73934 -> 73934`, no improvement.
- Step 11 LKH multi-seed: `seeds=1-20`, `RUNS=1`, best `73934`, no improvement.

Decision: prioritize solution quality now. Proof/lower-bound polish can wait.

## Chosen approach

Implement **B: runner + ETA + progress ledger + reports**.

Do not implement a web UI now. Terminal progress plus generated HTML report is enough and keeps scope focused on search quality.

## Success criteria

Primary:

```txt
best_verified_length < 73934
```

Operational:

- total job count is known before run starts;
- each job is bounded by `--job-timeout-minutes`;
- runner supports `--time-budget-hours`;
- runner prints progress, best-so-far, average runtime, and ETA;
- runner appends progress to JSONL after every job;
- runner can resume without repeating completed jobs;
- runner saves a best artifact immediately when it finds an improvement;
- non-best full portfolio result stays under `results/runs/`;
- final Markdown and HTML reports summarize results.

## Files

Create:

```txt
experiments/step12_lkh_portfolio.py
tests/test_step12_lkh_portfolio.py
notes/14-step12-lkh-portfolio.md
results/runs/step12-lkh-portfolio-progress.jsonl
results/runs/step12-lkh-portfolio.json
results/runs/step12-lkh-portfolio-report.html
```

Create only if improvement is found:

```txt
results/best/step12-lkh-portfolio-best.json
```

This plan file:

```txt
notes/14-step12-lkh-portfolio-plan.md
```

## Portfolio design

Use explicit, bounded jobs:

```txt
job = config_id × seed
```

Initial config set:

```txt
A_default_r3       RUNS=3
B_default_r5       RUNS=5
C_trials3000_r3    RUNS=3, MAX_TRIALS=3000
D_trials5000_r3    RUNS=3, MAX_TRIALS=5000
E_patch_r3         RUNS=3, PATCHING_C=3, PATCHING_A=2
F_move5_r3         RUNS=3, MOVE_TYPE=5
```

Initial seed set:

```txt
1-20
```

Initial total:

```txt
6 configs × 20 seeds = 120 jobs
```

Runner must support narrower subsets:

```bash
--configs A_default_r3,C_trials3000_r3
--seeds 1-5
```

## CLI shape

Calibration:

```bash
python experiments/step12_lkh_portfolio.py \
  --calibrate \
  --seeds 1-3
```

Main bounded run:

```bash
python experiments/step12_lkh_portfolio.py \
  --seeds 1-20 \
  --time-budget-hours 2 \
  --job-timeout-minutes 20
```

Resume:

```bash
python experiments/step12_lkh_portfolio.py \
  --seeds 1-20 \
  --time-budget-hours 2 \
  --job-timeout-minutes 20 \
  --resume
```

Targeted later wave:

```bash
python experiments/step12_lkh_portfolio.py \
  --configs A_default_r3,C_trials3000_r3 \
  --seeds 21-100 \
  --time-budget-hours 10 \
  --job-timeout-minutes 20 \
  --resume
```

## Progress output

Terminal output should be compact but informative:

```txt
Step 12 LKH Portfolio
[017/120] C_trials3000_r3 seed=8 done 93.4s len=73934 best=73934
elapsed: 00:27:14 | avg/job: 96.2s | ETA: 02:45:09 | budget left: 01:32:46
```

At minimum print after every job:

- job index / total;
- config id;
- seed;
- status;
- verified length or error;
- runtime;
- best so far;
- ETA;
- budget left if budget is set.

## Progress ledger

Append after every job:

```txt
results/runs/step12-lkh-portfolio-progress.jsonl
```

Each line schema:

```json
{
  "job_id": "C_trials3000_r3__seed_8",
  "job_index": 17,
  "jobs_total": 120,
  "config_id": "C_trials3000_r3",
  "seed": 8,
  "status": "done",
  "solver_length": 73934,
  "verified_length": 73934,
  "best_so_far": 73934,
  "runtime_seconds": 93.4,
  "elapsed_seconds": 1634.0,
  "eta_seconds": 9909.0,
  "parameter_file": "data/processed/lkh-step12-C_trials3000_r3-seed-8.par",
  "output_tour_file": "data/processed/lkh-step12-C_trials3000_r3-seed-8.tour",
  "created_at": "..."
}
```

Failure line schema:

```json
{
  "job_id": "...",
  "status": "failed",
  "error": "...",
  "runtime_seconds": 1200.0,
  "best_so_far": 73934
}
```

Timeouts are failures with `status = "timeout"`.

## Resume behavior

On `--resume`:

1. Read `results/runs/step12-lkh-portfolio-progress.jsonl` if present.
2. Extract completed job ids with status `done`, `failed`, or `timeout`.
3. Skip completed job ids.
4. Continue appending new lines.
5. Reconstruct best-so-far from completed `done` rows.

Without `--resume`:

- if progress ledger exists, fail fast with a clear message unless `--force` is provided;
- `--force` may overwrite old progress/result/report files for the same Step 12 run.

## Best artifact policy

If any job finds:

```txt
verified_length < 73934
```

immediately write/update:

```txt
results/best/step12-lkh-portfolio-best.json
```

Payload must include:

- algorithm: `lkh_2_0_11_portfolio`;
- input file;
- config id;
- seed;
- LKH parameters;
- verified length;
- previous upper bound `73934`;
- improvement amount;
- lower bound;
- absolute/relative gap;
- tour;
- parameter file;
- output tour file;
- command;
- created timestamp.

If no improvement is found, do not create a best artifact.

## Final result artifact

Always write:

```txt
results/runs/step12-lkh-portfolio.json
```

Payload should include:

- algorithm;
- job count planned/completed/skipped/failed/timeout;
- configs used;
- seed spec;
- time budget;
- job timeout;
- best verified length;
- best config/seed;
- whether current upper bound improved;
- length distribution;
- runtime distribution by config;
- all compact job records;
- path to progress ledger;
- path to HTML report.

Keep it compact. Do not embed full stdout for every job unless truncated to tail.

## Reports

### Markdown note

Create/update:

```txt
notes/14-step12-lkh-portfolio.md
```

Include:

- command used;
- configs and seeds;
- budget and timeout;
- total jobs completed;
- best result;
- whether it improved `73934`;
- length distribution;
- runtime summary;
- current interval after the run;
- recommended next step.

### HTML report

Create:

```txt
results/runs/step12-lkh-portfolio-report.html
```

Self-contained static HTML, no server.

Include:

- top summary cards;
- progress/best-over-time table;
- config × seed result table;
- length distribution table;
- runtime by config table.

No JS dependency required. Simple CSS is enough.

## Calibration mode

`--calibrate` should:

1. run a small subset, default `seeds=1-3` and all configs unless narrowed;
2. estimate average seconds/job overall and by config;
3. estimate full portfolio runtime for the requested config/seed set;
4. print the estimate;
5. write a calibration artifact under:

```txt
results/runs/step12-lkh-portfolio-calibration.json
```

Calibration should not create `results/best/step12-lkh-portfolio-best.json` unless explicitly run in normal mode. The purpose is timing estimation, not final result promotion.

## TDD implementation tasks

### Task 1 — RED tests for portfolio construction

Test:

- default config count is 6;
- seed spec parser supports `1-3` and `1,3,7`;
- job ids are stable;
- `configs × seeds` count is deterministic.

Expected initial failure: missing `experiments.step12_lkh_portfolio`.

### Task 2 — GREEN portfolio construction

Implement minimal:

- config dataclass/dict;
- seed parser;
- job builder;
- stable job id function.

Run focused tests.

### Task 3 — RED tests for ETA/progress math

Test:

- average runtime calculation;
- ETA from completed/remaining jobs;
- budget-left calculation;
- decision to not start a new job when estimated job time exceeds remaining budget.

### Task 4 — GREEN ETA/progress math

Implement pure helpers:

- `runtime_stats(records)`;
- `eta_seconds(completed, total, avg_seconds)`;
- `should_start_next_job(...)`.

Run focused tests.

### Task 5 — RED tests for ledger append/read/resume

Test:

- append JSONL record;
- read completed job ids;
- reconstruct best-so-far;
- `--resume` skips completed jobs;
- no-resume with existing ledger fails unless force.

### Task 6 — GREEN ledger/resume

Implement JSONL helpers and resume planner.

Run focused tests.

### Task 7 — RED tests for best artifact policy

Test:

- non-improving `73934` does not route to `results/best`;
- improving `73933` routes to best artifact;
- best payload contains verified length, config id, seed, params, previous upper bound, lower bound, and tour.

### Task 8 — GREEN best/result artifact policy

Implement payload builders and path policy.

Run focused tests.

### Task 9 — RED tests for report generation

Test:

- Markdown report includes command, best length, improvement status, distribution;
- HTML report includes summary, config table, length distribution, and runtime table.

### Task 10 — GREEN report generation

Implement Markdown and static HTML report writers.

Run focused tests.

### Task 11 — Integrate actual LKH job execution

Reuse Step 11 patterns:

- write TSPLIB file;
- write LKH parameter file;
- run `tools/LKH-2.0.11/LKH` with timeout;
- parse tour;
- verify with `tour_length(..., validate=True)`;
- append ledger record.

Do a smoke run:

```bash
python experiments/step12_lkh_portfolio.py \
  --configs A_default_r3 \
  --seeds 1 \
  --time-budget-hours 1 \
  --job-timeout-minutes 20 \
  --force
```

### Task 12 — Calibration smoke

Run:

```bash
python experiments/step12_lkh_portfolio.py \
  --calibrate \
  --configs A_default_r3 \
  --seeds 1 \
  --job-timeout-minutes 20 \
  --force
```

Verify calibration artifact exists and contains estimated runtime fields.

### Task 13 — Full verification

Run:

```bash
pytest -q
python - <<'PY'
import json
from pathlib import Path
p = Path('results/runs/step12-lkh-portfolio.json')
if p.exists():
    data = json.loads(p.read_text())
    assert data['algorithm'] == 'lkh_2_0_11_portfolio'
    assert 'best_verified_length' in data
print('step12_artifacts_ok')
PY
git diff --check
git status --short
```

### Task 14 — Commit

Commit implementation and plan/report artifacts after verification.

Suggested commit:

```bash
git add experiments/step12_lkh_portfolio.py \
        tests/test_step12_lkh_portfolio.py \
        notes/14-step12-lkh-portfolio-plan.md \
        notes/14-step12-lkh-portfolio.md \
        results/runs/step12-lkh-portfolio*.json \
        results/runs/step12-lkh-portfolio*.jsonl \
        results/runs/step12-lkh-portfolio-report.html \
        README.md AGENTS.md notes/07-next-experiments-plan.md

git commit -m "Add LKH portfolio runner with progress reporting"
```

Adjust `git add` to actual created files.

## First real run after implementation

Start with a bounded 1-2h run:

```bash
python experiments/step12_lkh_portfolio.py \
  --seeds 1-20 \
  --time-budget-hours 2 \
  --job-timeout-minutes 20 \
  --force
```

If it finds improvement, stop and document the new upper bound.

If it does not improve but identifies promising configs, run targeted long wave:

```bash
python experiments/step12_lkh_portfolio.py \
  --configs <best-two-configs> \
  --seeds 21-100 \
  --time-budget-hours 10 \
  --job-timeout-minutes 20 \
  --resume
```

## Stop rules

Stop or reconsider if:

- best remains `73934` after 100-200 bounded jobs;
- most configs repeatedly return worse than `73934`;
- runtime per job exceeds the budget assumptions by more than 2×;
- the runner detects repeated timeouts for the same config.

If no upper-bound improvement after the portfolio, switch to final-result preparation and optionally one lower-bound tuning wave.
