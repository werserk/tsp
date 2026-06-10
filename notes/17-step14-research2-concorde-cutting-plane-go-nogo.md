# Step 14 / Research 2 — Concorde / subtour-LP / cutting-plane LB go-no-go memo

Дата: 2026-06-10

## Objective

Determine whether Concorde or another open-source cutting-plane/subtour-LP workflow can produce a valid lower bound for the 1114-city `FULL_MATRIX` symmetric TSP instance:

```txt
input: data/raw/matrices/M.txt
n: 1114
current verified LB: 72711.81768955325
current verified UB: 73934
success for promotion: reported_lower_bound > 72711.81768955325 and <= 73934
```

This memo covers **Research 2 only**. It does not start the Held-Karp portfolio.

## Sources inspected

1. Concorde official download page:
   `https://www.math.uwaterloo.ca/tsp/concorde/downloads/downloads.htm`
   - Source and executables are available for academic research use.
   - Concorde executable is the cutting-plane-based exact TSP solver using QSopt.
   - Linux executable listed, but old Red Hat Linux 8.0 build.

2. Concorde README / installation guide:
   `https://www.math.uwaterloo.ca/tsp/concorde/DOC/README.html`
   - Build flow: unpack source, `./configure`, `make`.
   - LP backend is required for the TSP solver route; `--with-qsopt=DIR` expects a directory containing `qsopt.a` and `qsopt.h`.
   - QSopt and CPLEX are supported LP backend options.

3. Concorde source mirror, `TSP/concorde.c`:
   `https://raw.githubusercontent.com/matthelb/concorde/master/TSP/concorde.c`
   - CLI options include:
     - `-B` do not branch;
     - `-I` just solve the subtour polytope;
     - `-w` just subtours and trivial blossoms;
     - `-X f` write the last root fractional solution;
     - `-u v` initial upper bound;
     - `-o f` output optimal tour;
     - `-N 7` matrix norm for non-TSPLIB matrix input;
     - default input mode is TSPLIB.
   - Output strings include:
     - `Final lower bound %f, upper bound %f`;
     - `Exact lower bound: %.6f`;
     - `Final LP has %d rows, %d columns, %d nonzeros`;
     - `Optimal Solution: %.2f` when Concorde proves optimality.

4. Concorde source mirror, `UTIL/getdata.c`:
   `https://raw.githubusercontent.com/matthelb/concorde/master/UTIL/getdata.c`
   - TSPLIB `EDGE_WEIGHT_TYPE: EXPLICIT` maps to `CC_MATRIXNORM`.
   - `EDGE_WEIGHT_FORMAT: FULL_MATRIX` is explicitly parsed.
   - Concorde reads all `n*n` matrix entries for `FULL_MATRIX` and internally stores a triangular representation. This is compatible with our symmetric full matrix.

5. QSopt official download page:
   `https://www.math.uwaterloo.ca/~bico/qsopt/downloads/downloads.htm`
   - Linux 2.4 artifacts include `qsopt.a.gz` and `qsopt.h` under `codes/linux24/`.
   - These are old binaries; source/build compatibility is the main risk.

6. HiGHS / `highspy` docs and PyPI metadata:
   `https://ergo-code.github.io/HiGHS/stable/interfaces/python/`
   `https://pypi.org/project/highspy/`
   - Install path is `pip install highspy`.
   - HiGHS solves LP/MIP models, but it does not provide a TSP cutting-plane workflow by itself.

7. NetworkX Stoer-Wagner min-cut docs:
   `https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.connectivity.stoerwagner.stoer_wagner.html`
   - Usable for subtour-cut separation in an in-house DFJ LP loop, but this would be a custom implementation, not a ready solver route.

## Local availability check

Current environment does not have the required solver binaries/packages installed:

```txt
concorde: missing
linkern: missing
highs: missing
highspy: missing
networkx: missing
scipy: missing
```

## FULL_MATRIX mapping

Our source file is plain project format:

```txt
first line: n
next n lines: n integer distances per row
```

Concorde should receive TSPLIB explicit matrix format:

```txt
NAME: hse1114
TYPE: TSP
COMMENT: Converted from data/raw/matrices/M.txt
DIMENSION: 1114
EDGE_WEIGHT_TYPE: EXPLICIT
EDGE_WEIGHT_FORMAT: FULL_MATRIX
EDGE_WEIGHT_SECTION
<1114 rows × 1114 integer distances>
EOF
```

Exact conversion command:

```bash
cd /home/werserk/3-education/hse/combinatorial-optimization/tsp
mkdir -p data/processed results/runs
python - <<'PY'
from pathlib import Path
from src.io.matrix_loader import load_matrix

inp = Path('data/raw/matrices/M.txt')
out = Path('data/processed/M-full-matrix.tsplib')
data = load_matrix(inp)
with out.open('w', encoding='utf-8') as f:
    f.write('NAME: hse1114\n')
    f.write('TYPE: TSP\n')
    f.write(f'COMMENT: Converted from {inp}\n')
    f.write(f'DIMENSION: {data.n}\n')
    f.write('EDGE_WEIGHT_TYPE: EXPLICIT\n')
    f.write('EDGE_WEIGHT_FORMAT: FULL_MATRIX\n')
    f.write('EDGE_WEIGHT_SECTION\n')
    for row in data.matrix:
        f.write(' '.join(map(str, row)) + '\n')
    f.write('EOF\n')
print(out)
PY
```

Expected checks before running Concorde:

```bash
python - <<'PY'
from pathlib import Path
p = Path('data/processed/M-full-matrix.tsplib')
text = p.read_text(encoding='utf-8').splitlines()
assert 'DIMENSION: 1114' in text[:10]
assert 'EDGE_WEIGHT_TYPE: EXPLICIT' in text[:10]
assert 'EDGE_WEIGHT_FORMAT: FULL_MATRIX' in text[:10]
assert text[-1] == 'EOF'
print('tsplib_ok', p, p.stat().st_size)
PY
```

## Concorde route

### Build/install option 1 — prebuilt binary smoke test

Fastest path, but old Linux binary may not run on current Arch/glibc.

```bash
cd /home/werserk/3-education/hse/combinatorial-optimization/tsp
mkdir -p tools/concorde-bin
cd tools/concorde-bin
curl -L -o concorde.gz https://www.math.uwaterloo.ca/tsp/concorde/downloads/codes/linux24/concorde.gz
gunzip -f concorde.gz
chmod +x concorde
./concorde 2>&1 | tee ../../results/runs/concorde-help.txt
```

Expected success signal:

```txt
Usage: ./concorde [-see below-] [dat_file]
```

Build risk:

```txt
old Red Hat Linux 8.0 executable may fail on modern Arch Linux;
if it fails, do not debug ABI issues for long — switch to source build.
```

### Build/install option 2 — source build with QSopt

More reproducible, but highest integration risk.

```bash
cd /home/werserk/3-education/hse/combinatorial-optimization/tsp
mkdir -p tools/concorde-src tools/qsopt
cd tools/qsopt
curl -L -O https://www.math.uwaterloo.ca/~bico/qsopt/downloads/codes/linux24/qsopt.a.gz
curl -L -O https://www.math.uwaterloo.ca/~bico/qsopt/downloads/codes/linux24/qsopt.h
gunzip -f qsopt.a.gz

cd ../concorde-src
curl -L -O https://www.math.uwaterloo.ca/tsp/concorde/downloads/codes/src/co031219.tgz
tar xzf co031219.tgz
cd concorde
CC=gcc CFLAGS='-O3' ./configure --with-qsopt="$(cd ../../qsopt && pwd)"
make
./TSP/concorde 2>&1 | tee ../../../results/runs/concorde-source-help.txt
```

Expected success signal:

```txt
Usage: ./TSP/concorde [-see below-] [dat_file]
```

Build risks:

```txt
1. QSopt Linux artifacts are also old Linux binaries/libraries.
2. Concorde source is from 2003; modern compiler warnings may become build failures.
3. If QSopt archive is incompatible, source build blocks unless we patch/link a compatible LP backend.
4. License: academic research use is fine for coursework; other use requires licensing contact.
```

### Concorde lower-bound run commands

Recommended first run is **no branching** with current upper bound. This targets a valid root/cutting-plane lower bound without committing to exact solve runtime.

```bash
cd /home/werserk/3-education/hse/combinatorial-optimization/tsp
CONCORDE=tools/concorde-bin/concorde  # or tools/concorde-src/concorde/TSP/concorde
PYTHONUNBUFFERED=1 "$CONCORDE" \
  -B \
  -u 73934 \
  -X results/runs/step14-concorde-root.x \
  -o results/runs/step14-concorde-tour.out \
  data/processed/M-full-matrix.tsplib \
  2>&1 | tee results/runs/step14-concorde-root.log
```

Expected output fields to parse:

```txt
Final lower bound <lb>, upper bound <ub>
Exact lower bound: <exact_lb>
Final LP has <rows> rows, <columns> columns, <nonzeros> nonzeros
```

Interpretation:

```txt
lower_bound_candidate = max(parsed Final lower bound, parsed Exact lower bound if present)
upper_bound_candidate = parsed upper bound; do not confuse this with lower bound
rows/columns/nonzeros = audit metadata for the LP/cuts produced
```

Promotion gate:

```txt
parsed_lb > 72711.81768955325
parsed_lb <= 73934
log saved under results/runs/
TSPLIB converter path recorded
proof note: root LP/cutting-plane relaxation is a lower bound because it relaxes the integer TSP polytope; branch-and-cut lower bounds remain lower bounds until optimality is proved
```

If root cut run finishes fast but LB is below Step 13, one more no-branch variant is worth trying:

```bash
PYTHONUNBUFFERED=1 "$CONCORDE" \
  -B -w -u 73934 \
  -X results/runs/step14-concorde-subtour-blossom.x \
  data/processed/M-full-matrix.tsplib \
  2>&1 | tee results/runs/step14-concorde-subtour-blossom.log
```

Notes:

```txt
-I = just solve subtour polytope; useful diagnostic, likely weaker than full cut loop.
-w = just subtours and trivial blossoms; useful controlled run.
Default -B without -I/-w is preferred for strongest root cutting-plane LB.
```

### Optional exact/reference run

Only after no-branch run succeeds and time allows:

```bash
PYTHONUNBUFFERED=1 "$CONCORDE" \
  -u 73934 \
  -o results/runs/step14-concorde-opt.tour \
  data/processed/M-full-matrix.tsplib \
  2>&1 | tee results/runs/step14-concorde-opt.log
```

Expected extra output if exact solve succeeds:

```txt
Optimal Solution: <value>
Number of bbnodes: <count>
```

This may run too long; do not make exact solve the first integration target.

## Alternative route — HiGHS subtour LP

Feasible but not recommended as first implementation.

### Exact commands for a prototype install

```bash
cd /home/werserk/3-education/hse/combinatorial-optimization/tsp
python -m venv .venv-tsp-lp
source .venv-tsp-lp/bin/activate
pip install highspy networkx
```

### Workflow

1. Create undirected edge variables `x_ij` for all `i < j`: about `1114*1113/2 = 620241` variables.
2. Degree constraints:

```txt
sum_j x_ij = 2 for every city i
0 <= x_ij <= 1
```

3. Solve LP with HiGHS.
4. Build support graph from `x_ij > eps` and separate subtour cuts / min-cuts:

```txt
sum_{i in S, j not in S} x_ij >= 2
```

5. Add violated cuts and repeat until no violated subtour cut remains.
6. LP objective is a valid lower bound for TSP.

### Expected output fields

```txt
iteration
lp_status
objective_value
num_variables
num_degree_constraints
num_subtour_cuts_added
min_cut_value
runtime_seconds
```

### Risks

```txt
1. This is a custom cutting-plane implementation, not a ready solver.
2. 620k variables plus iterative min-cut separation may be memory/time-heavy.
3. Without blossom/comb cuts it may be weaker than Concorde and may not beat Step 13.
4. More code and tests are needed before the number is presentation-safe.
```

## Alternative route — SCIP/MIP

Not recommended now.

Possible shape:

```txt
build binary MILP with x_ij ∈ {0,1}, degree constraints, lazy subtour elimination callbacks
```

Risk:

```txt
For 1114 nodes, full binary TSP has ~620k binary variables. SCIP can report dual bounds during branch-and-cut, but integrating callbacks/cut separation is heavier than Concorde and likely slower for this course task.
```

## Go/no-go recommendation

Recommendation: **A) implement Concorde route now**, but only as a time-boxed integration smoke + no-branch lower-bound extraction.

Why:

1. Concorde explicitly supports TSPLIB `EXPLICIT` + `FULL_MATRIX` input.
2. Concorde CLI exposes exactly the lower-bound fields we need:

```txt
Final lower bound ...
Exact lower bound: ...
Final LP has ...
```

3. `-B` gives a bounded no-branch root/cutting-plane run, so we can extract a valid lower bound without waiting for a full exact solve.
4. It is an independent bound family from Held-Karp and can either improve the gap or calibrate whether Step 13 is already close to the practical root LP bound.
5. HiGHS/SCIP alternatives require custom cutting-plane infrastructure and are slower to make trustworthy.

## Stop / fallback rule

Use this decision gate:

```txt
If Concorde executable/source build does not reach a working `concorde` binary within 60–90 minutes, stop Concorde integration and return to Held-Karp portfolio.
If Concorde runs but root/cut lower bound <= 72711.81768955325, archive the log as a negative result and return to Held-Karp portfolio or Polyak schedule.
If Concorde reports lower bound > 72711.81768955325 and <= 73934, implement parser + verifier note and promote a new Step 14 best LB artifact.
```

## Verdict

Go: **A) implement Concorde route now**.

Do not choose B unless Concorde build is blocked. Do not choose C until Concorde has either failed to build/run within the time box or produced a non-improving lower bound.
