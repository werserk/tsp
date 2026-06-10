# Agent Map

Short instructions for coding agents working on this TSP project.

## First Reads

- `README.md` — project goal, folder map, and first workflow rules.
- `notes/00-lecturer-brief.md` — lecturer's exact challenge and presentation format.
- `notes/01-tsp-basics-and-development-plan.md` — beginner-friendly TSP concepts, bounds, and baseline development plan.
- `notes/02-step1-data-audit.md` — verified matrix formats, dimensions, symmetry, and value ranges.
- `notes/03-step2-core-infrastructure.md` — matrix loader, validation, tour length contract, and smoke checks.
- `notes/04-step3-nearest-neighbor-baseline.md` — first valid upper bound from multi-start nearest neighbor.
- `notes/05-step4-two-opt-improvement.md` — 2-opt local search improvement and current best upper bound.
- `notes/06-step5-lower-bound-mst-one-tree.md` — MST / 1-tree lower-bound proof and current optimality interval.
- `notes/07-next-experiments-plan.md` — prioritized next experiments: LKH, several-root 1-tree, multi-start 2-opt, Held-Karp-style penalties.
- `notes/08-step6-lkh-benchmark.md` — LKH benchmark and current best upper bound `73934`.
- `notes/09-step7-several-root-one-tree.md` — sampled several-root 1-tree proof and current best lower bound `63494`.
- `notes/10-step8-multistart-two-opt.md` — own NN-ranked multi-start 2-opt check; useful backup but weaker than LKH.
- `notes/11-step9-held-karp-one-tree.md` — Held-Karp-style 1-tree penalties; current best lower bound `65493.437369`.
- `notes/12-step10-restricted-three-opt.md` — restricted 3-opt/LK-like local search check; no improvement over LKH.
- `notes/13-step11-lkh-multiseed.md` — LKH multi-seed upper-bound search; seeds `1-20` did not improve `73934`.
- `notes/14-step12-lkh-portfolio-plan.md` — bounded LKH portfolio runner implementation plan.
- `notes/14-step12-lkh-portfolio.md` — Step 12 smoke portfolio report; use `experiments/step12_lkh_portfolio.py` for ETA/progress/resume waves.
- `docs/playbooks/tsp-lower-bound-improvement.md` — required playbook for metric-driven lower-bound improvement cycles.
- `docs/playbooks/tsp-upper-bound-improvement.md` — required playbook for metric-driven upper-bound improvement cycles.
- `docs/playbooks/tsp-experiment-protocol.md` — experiment artifact, verification, and promotion protocol.
- `docs/playbooks/tsp-result-review-gate.md` — review gate before claiming a new best bound.
- `docs/goals/improve-tsp-lower-bound.goal.md` — ready `/goal` prompt for aggressive-local lower-bound improvement.
- `docs/goals/improve-tsp-upper-bound.goal.md` — ready `/goal` prompt for aggressive-local upper-bound improvement.
- `data/raw/matrices/README.md` — observed matrix formats and canonical challenge size.
- `references/lecturer-code/` — lecturer-provided Python examples; read as reference, do not edit in place.

## Goal

Produce the best defensible bounds for the Travelling Salesman Problem challenge:

- **Upper bound:** a valid tour and its length.
- **Lower bound:** a mathematically valid bound with a short explanation.
- **Final explanation:** 15-minute blackboard/code talk, no slides.

## Data Rules

- Treat `data/raw/**` as read-only.
- Main challenge input: `data/raw/matrices/M.txt`.
- Canonical challenge size: `1114` cities; `M.txt` parses as `1114×1114`.
- Put normalized caches and derived inputs under `data/processed/`.
- Every result must record the exact input file used.

## Code Rules

- Put new code under `src/`; do not modify lecturer code directly.
- Keep matrix parsing in `src/io/`.
- Put upper-bound algorithms in `src/heuristics/`.
- Put lower-bound algorithms in `src/bounds/`.
- Prefer deterministic, reproducible scripts: fixed seeds, explicit parameters, saved commands.
- For performance experiments, separate algorithm code from run/config code.

## Result Rules

- Save ordinary run logs under `results/runs/`.
- Save only current best artifacts under `results/best/`.
- A best upper-bound artifact must include: tour order, tour length, input matrix, algorithm, parameters, seed, date.
- A best lower-bound artifact must include: bound value, method, proof/justification sketch, input matrix, date.

## Experiment Rules

- Put reproducible run scripts/configs under `experiments/`.
- Do not leave important results only in notebooks or terminal output.
- If a notebook finds something useful, promote the method/result into `src/`, `experiments/`, or `results/`.

## Validation Checklist

Before reporting a bound:

- Matrix loaded with expected shape.
- Distances interpreted consistently with the source file format.
- Upper-bound tour visits every city exactly once and returns to start.
- Tour length recomputed independently from the matrix.
- Lower-bound method is valid for the exact TSP variant represented by the matrix.
- Result file contains enough metadata to rerun or explain the result.

## Useful Starting Tasks

1. Implement a robust matrix loader in `src/io/`.
2. Add a verifier for tours and tour length.
3. Establish a baseline upper bound: nearest neighbor + 2-opt/3-opt.
4. Establish a baseline lower bound: MST/1-tree or assignment relaxation.
5. Create a compact `results/best/summary.md` once first bounds exist.
