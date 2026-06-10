# TSP Result Review Gate

## Purpose

Prevent weak, invalid, or unverifiable results from being presented as improvements.

Use this gate before saying a TSP experiment improved the current best lower bound, upper bound, or gap.

## Current best values

```txt
lower_bound: 65493.4373688764
upper_bound: 73934
absolute_gap: 8440.562631123597
relative_gap_to_lower: 12.887646411936071%
relative_gap_to_upper: 11.416347865831144%
```

## Gate 1 — identify result type

Classify the result:

```txt
A) feasible tour / upper bound
B) relaxation or certificate / lower bound
C) solver diagnostic only
D) research finding only
E) implementation improvement only
```

Only A or B can improve the gap directly.

## Gate 2 — verify strict improvement

Upper-bound improvement:

```txt
candidate_upper_bound < 73934
```

Lower-bound improvement:

```txt
candidate_lower_bound > 65493.4373688764
candidate_lower_bound <= 73934
```

If the candidate ties the current best, save as run evidence, not best.

## Gate 3 — validate correctness

### Upper-bound checks

- tour has length exactly `1114`;
- every city index appears exactly once;
- tour length is recomputed from `data/raw/matrices/M.txt`;
- recomputed length equals artifact length;
- command and parameters are saved.

### Lower-bound checks

- proof/validity sketch exists;
- relaxation/certificate applies to the exact matrix and TSP variant;
- value is not above the known upper bound;
- numerical precision/rounding is handled conservatively;
- independent recomputation or solver-log audit is documented.

## Gate 4 — artifact quality

A promotable artifact must include:

```txt
algorithm/method
input path
metric value
previous best
command
parameters/config
runtime
verification method
created_at
```

Lower-bound artifacts must additionally include:

```txt
proof_sketch
validity assumptions
precision/rounding policy
```

## Gate 5 — documentation update

If promoted:

- update `README.md` current bounds;
- update `AGENTS.md` first reads if a new durable note was added;
- write or update a step note under `notes/`;
- keep only current best artifacts in `results/best/`.

If rejected or non-improving:

- keep artifact/log under `results/runs/`;
- write a negative result note if the experiment was costly or informs next steps;
- do not update current bounds.

## Review verdict template

```md
Status: accepted | rejected | needs rerun
Type: upper_bound | lower_bound | diagnostic
Candidate value: <number>
Current best: <number>
Strict improvement: yes | no
Verification: passed | failed | partial
Decision: promote | keep in runs | discard | rerun
Reason: <short evidence>
Next: <one action>
```
