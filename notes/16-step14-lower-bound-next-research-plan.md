# Step 14 — Lower-bound next research and experiment plan

Дата: 2026-06-10

## Objective

Сформировать следующий проверяемый цикл улучшения lower bound после Step 13.

Текущий verified interval:

```txt
72711.81768955325 <= OPT <= 73934
integer interval: 72712 <= OPT <= 73934
absolute_gap: 1222.1823104467476
relative_gap_to_lower: 1.680857870538894%
relative_gap_to_upper: 1.6530720784033701%
```

Текущий best lower-bound artifact:

```txt
results/best/step13-held-karp-decay-099-lower-bound.json
```

## Verdict

Следующее развитие есть, но потенциал уже ограничен текущим upper bound: lower bound может вырасти максимум на `1222.1823104467476`.

Лучший следующий ход:

1. **Immediate experiment:** дожать Held-Karp/Lagrangian 1-tree schedule portfolio, потому что Step 13 best был на последней итерации (`best_iteration=999`).
2. **Parallel research:** изучить subtour LP / cutting-plane / Concorde route как независимую и потенциально более сильную lower-bound family.
3. **Secondary research:** изучить open-source workflows для ~1000-node symmetric TSP, чтобы понять, где быстрее всего получить дополнительный gap reduction.

## Why Held-Karp continuation is first

Step 13 parameters:

```txt
iterations: 1000
initial_step_size: 64.0
step_decay: 0.99
best_iteration: 999
runtime_seconds: 387.290
```

`best_iteration=999` означает, что текущий schedule не показал явного plateau внутри выделенных 1000 итераций. Поэтому перед более сложной polyhedral integration стоит провести bounded portfolio вокруг schedule/iterations/root/start choices.

## Research 1 — Held-Karp ascent tuning

### Research question

```txt
What subgradient / step-size / volume algorithm variants are used to maximize Held-Karp 1-tree TSP lower bounds?
```

### Sources to inspect

- papers/surveys on Held-Karp lower bound for TSP;
- implementation notes for Lagrangian 1-tree ascent;
- references on subgradient optimization schedules;
- volume algorithm / stabilized Lagrangian methods;
- any open-source implementations exposing multiplier update rules.

### Extract from each source

```txt
method:
step-size formula:
multiplier initialization:
stopping rule:
whether it reports best-so-far or last iterate:
expected runtime behavior:
implementation complexity:
risk/pitfall:
```

### Expected output

A ranked set of 3–5 implementable schedules, for example:

```txt
A) longer slow decay: decay ∈ {0.992, 0.995, 0.997}, iterations ∈ {3000, 5000}
B) adaptive step-size based on degree violation norm
C) multiple multiplier starts / root variants
D) volume or stabilized subgradient update
```

### Immediate experiment candidate

Run a bounded portfolio such as:

```txt
step_decay ∈ {0.992, 0.995, 0.997}
iterations ∈ {3000, 5000}
initial_step_size ∈ {32, 64, 128}
root_city ∈ {0 plus selected alternatives if cheap}
```

Required artifact behavior:

- append progress ledger after each config;
- save best penalties for independent recomputation;
- promote only if `lower_bound > 72711.81768955325`;
- preserve non-improvements under `results/runs/`.

## Research 2 — Concorde / subtour LP / cutting-plane lower bound extraction

### Research question

```txt
Can Concorde or related open-source TSP solvers expose a valid lower bound/certificate for a TSPLIB FULL_MATRIX instance?
```

### Sources to inspect

- Concorde TSP Solver docs/readme/build notes;
- Concorde command-line options and logs;
- QSopt/LP dependency notes;
- examples of extracting lower bounds or optimality certificates;
- SCIP/HiGHS/other LP/MIP routes for subtour relaxation if Concorde is blocked.

### Extract from each source

```txt
build requirements:
input format support:
FULL_MATRIX compatibility:
command to run:
where lower bound appears:
whether certificate/proof is available:
how to distinguish tour length vs lower bound:
runtime expectations for ~1114 nodes:
license/install risk:
```

### Expected output

One of:

```txt
A) reproducible local Concorde integration plan;
B) alternative solver integration plan;
C) explicit reject reason with evidence.
```

### Acceptance requirements

- exact mapping from `data/raw/matrices/M.txt` to solver input;
- solver output/log saved under `results/runs/`;
- lower bound parsed separately from upper bound/tour;
- proof/audit note explaining why the reported number is a valid lower bound;
- promotion only if verified `lower_bound > 72711.81768955325`.

## Research 3 — Best practical workflows for ~1000-node symmetric TSP

### Research question

```txt
For ~1000-node symmetric TSP with explicit integer distance matrix, what open-source heuristic/exact workflows usually improve UB/LB fastest?
```

### Sources to inspect

- solver documentation and benchmark reports for LKH, Concorde, EAX, SCIP/OR-Tools where relevant;
- GitHub repositories with reproducible TSP CLI workflows;
- papers or project notes comparing heuristics/exact solvers around 1000-node instances;
- any examples involving explicit distance matrices or TSPLIB FULL_MATRIX.

### Extract from each source

```txt
solver/method:
UB/LB/both:
input format:
expected runtime:
quality signal:
how outputs are verified:
integration complexity:
fit for this project:
```

### Expected output

A short ranked workflow list:

```txt
1. best immediate LB route
2. best immediate UB route
3. best exact/reference route
4. routes to avoid now
```

This research should feed both lower-bound and upper-bound goal processes.

## Step 14 execution shape

Recommended Step 14 goal prompt:

```txt
Primary objective:
Improve verified lower bound above 72711.81768955325.

First experiment:
Run Held-Karp schedule portfolio because Step 13 best_iteration=999 indicates ascent was still improving.

Parallel research:
Investigate Concorde/cutting-plane lower-bound extraction as the next independent bound family.

Success:
new verified LB > 72711.81768955325.

Stop:
schedule portfolio plateaus and Concorde/cutting-plane route is either integrated or rejected with evidence.
```

## Success criteria

Step 14 is successful only if one of these happens:

1. a new verified lower bound strictly above `72711.81768955325` is promoted to `results/best/`;
2. a high-confidence next method is selected with enough evidence to justify implementation;
3. all three research tracks produce evidence-based rejection/deferral notes.

Research alone is not enough unless it directly selects or rejects the next experiment with evidence.

## Risks

- Held-Karp schedule portfolio may plateau quickly and produce only small gains.
- Concorde/cutting-plane integration may take longer than the remaining course value justifies.
- External solver logs may expose bounds that are hard to certify without understanding solver semantics.
- Parallel UB/LB processes must reload current best artifacts before final gap reporting.

## Next action

Launch a Step 14 lower-bound goal using this plan and `docs/playbooks/tsp-lower-bound-improvement.md`.
