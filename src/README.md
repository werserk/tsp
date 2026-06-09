# Source code

Новый код проекта. Код лектора лежит отдельно в `../references/lecturer-code/` и не редактируется напрямую.

## Current modules

```txt
heuristics/nearest_neighbor.py  # deterministic nearest-neighbor upper-bound baseline
io/exceptions.py                # parse/validation exception classes
io/matrix_loader.py             # format detection and matrix loading
io/validation.py                # matrix and tour validation contracts
tsp/constants.py                # canonical paths, sizes, and format names
tsp/tour.py                     # independent tour length calculation
tsp/types.py                    # shared City/Distance/Matrix/Tour aliases
```

Tour contract: a tour is a permutation of `0..n-1`; the return edge to the first city is implicit.

Use `tour_length(..., validate=False)` only inside hot paths after inputs were already validated; final reported results should be recalculated with validation enabled.
