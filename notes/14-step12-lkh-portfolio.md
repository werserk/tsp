# Step 12 — LKH portfolio search

## Command

```bash
python experiments/step12_lkh_portfolio.py --seeds 1-20 --time-budget-hours 2 --job-timeout-minutes 20 --resume
```

## Summary

```txt
best_verified_length: 73934
best_config_id: A_default_r3
best_seed: 1
improved_current_upper_bound: false
jobs_completed: 87
jobs_failed: 0
jobs_timeout: 0
```

## Length distribution

- 73934: 83
- 73941: 3
- 73947: 1

## Runtime by config

| config | count | avg seconds | min | max |
|---|---:|---:|---:|---:|
| A_default_r3 | 20 | 81.267 | 45.346 | 96.804 |
| B_default_r5 | 20 | 128.999 | 88.515 | 164.370 |
| C_trials3000_r3 | 20 | 202.317 | 161.310 | 314.430 |
| D_trials5000_r3 | 20 | 328.523 | 290.897 | 423.075 |
| E_patch_r3 | 7 | 73.684 | 61.341 | 103.424 |

## Current interval

```txt
65493.437369 <= OPT <= 73934
```

## Recommended next step

If no improvement was found, use the runtime table to select the best 1-2 configs for a longer targeted wave, or stop upper-bound search and prepare the final explanation.
