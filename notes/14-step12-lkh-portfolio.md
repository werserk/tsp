# Step 12 — LKH portfolio search

## Command

```bash
python experiments/step12_lkh_portfolio.py --configs A_default_r3 --seeds 1-3 --time-budget-hours 1 --job-timeout-minutes 20 --resume
```

## Summary

```txt
best_verified_length: 73934
best_config_id: A_default_r3
best_seed: 1
improved_current_upper_bound: false
jobs_completed: 3
jobs_failed: 0
jobs_timeout: 0
```

## Length distribution

- 73934: 2
- 73941: 1

## Runtime by config

| config | count | avg seconds | min | max |
|---|---:|---:|---:|---:|
| A_default_r3 | 3 | 59.873 | 42.674 | 83.964 |

## Current interval

```txt
65493.437369 <= OPT <= 73934
```

## Recommended next step

If no improvement was found, use the runtime table to select the best 1-2 configs for a longer targeted wave, or stop upper-bound search and prepare the final explanation.
