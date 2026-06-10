# TSP Experiment Protocol

## Purpose

Keep every TSP experiment reproducible, auditable, and safe to compare against the current best bounds.

This protocol applies to both upper-bound and lower-bound work, with stricter proof requirements for lower bounds.

## Canonical input

```txt
challenge_matrix: data/raw/matrices/M.txt
canonical_size: 1114 cities
raw_data_policy: data/raw/** is read-only
```

Derived files may be written under `data/processed/`.

## Experiment lifecycle

### 1. Define the target

Record before running:

```txt
experiment_name:
metric: upper_bound | lower_bound | runtime | verifier_only
baseline_artifact:
success_condition:
expected_runtime:
```

For lower-bound experiments, success usually means:

```txt
new_lower_bound > 65493.4373688764
```

For upper-bound experiments, success usually means:

```txt
new_upper_bound < 73934
```

### 2. Prepare reproducible command

Every experiment must have a command that can be copied and rerun from repo root.

Example:

```bash
python experiments/<script>.py --arg value
```

Long runs should support at least one of:

- `--resume`;
- append-only progress ledger;
- bounded seed/config chunks;
- explicit timeout/budget args.

### 3. Write artifacts

Use:

```txt
results/runs/     ordinary runs, diagnostics, negative results
results/best/     only current best verified results
```

Do not keep important results only in terminal output or notebooks.

### 4. Verify independently

Upper-bound result:

- tour visits each city exactly once;
- tour length is recomputed from `M.txt` by project verifier;
- saved length equals recomputed length.

Lower-bound result:

- method has a proof/validity note;
- result is valid for the symmetric TSP represented by `M.txt`;
- value does not exceed current upper bound;
- independent recomputation/audit is performed when feasible.

### 5. Promote or reject

Promote only strict improvements.

If not improved, keep under `results/runs/` and write a short negative result note when the run was expensive or strategically important.

## Required JSON fields

### Upper-bound best artifact

```json
{
  "type": "upper_bound",
  "algorithm": "...",
  "length": 73934,
  "previous_upper_bound": 80585,
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

### Lower-bound best artifact

```json
{
  "type": "lower_bound",
  "algorithm": "...",
  "lower_bound": 65493.4373688764,
  "previous_lower_bound": 63494,
  "upper_bound": 73934,
  "input_matrix": "data/raw/matrices/M.txt",
  "proof_sketch": "...",
  "verification": "...",
  "command": "...",
  "parameters": {},
  "runtime_seconds": 0.0,
  "created_at": "..."
}
```

## Gap calculation

Use these formulas:

```txt
absolute_gap = upper_bound - lower_bound
relative_gap_to_lower = (upper_bound - lower_bound) / lower_bound
relative_gap_to_upper = (upper_bound - lower_bound) / upper_bound
```

For integer-friendly reporting:

```txt
integer_lower = ceil(lower_bound)
integer_interval = integer_lower <= OPT <= upper_bound
integer_gap = upper_bound - integer_lower
```

## Long-run discipline

For long experiments:

1. Run in chunks that can be resumed.
2. Save progress after every completed job.
3. Use unbuffered logs when foreground diagnostics are needed:

```bash
PYTHONUNBUFFERED=1 python experiments/<script>.py ... 2>&1 | tee results/runs/<name>.log
```

4. Avoid relying only on Hermes process registry for multi-hour jobs; preserve a file log/ledger.
5. After interruption, inspect OS process state and ledger before deciding to restart.

## Negative result note

Use this template when an important attempt fails to improve:

```md
# Step XX — <method> negative result

## Objective
## Why this method was plausible
## Command and parameters
## Verification
## Result
## Why it did not improve the current best
## Whether to retry later
```

## Promotion checklist

Before updating `results/best/` or README:

- [ ] strict improvement vs current best;
- [ ] independent verification passed;
- [ ] artifact contains command/input/parameters/runtime;
- [ ] proof note exists for lower bound;
- [ ] current interval remains valid;
- [ ] README/AGENTS/notes index updated if this becomes a durable step.
