# Source code

Новый код проекта. Код лектора лежит отдельно в `../references/lecturer-code/` и не редактируется напрямую.

## Current modules

```txt
bounds/mst.py                  # deterministic Prim MST lower-bound utility
bounds/one_tree.py             # fixed-root 1-tree lower-bound baseline
heuristics/nearest_neighbor.py  # deterministic nearest-neighbor upper-bound baseline
heuristics/two_opt.py           # deterministic 2-opt local search improvement
integrations/lkh.py             # TSPLIB export, LKH tour parsing, LKH result artifacts
io/exceptions.py                # parse/validation exception classes
io/matrix_loader.py             # format detection and matrix loading
io/validation.py                # matrix and tour validation contracts
tsp/constants.py                # canonical paths, sizes, and format names
tsp/tour.py                     # independent tour length calculation
tsp/types.py                    # shared City/Distance/Matrix/Tour aliases
```

Tour contract: a tour is a permutation of `0..n-1`; the return edge to the first city is implicit.

Use `tour_length(..., validate=False)` only inside hot paths after inputs were already validated; final reported results should be recalculated with validation enabled.
