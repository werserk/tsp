# Source code

Новый код проекта. Код лектора лежит отдельно в `../references/lecturer-code/` и не редактируется напрямую.

## Current modules

```txt
io/matrix_loader.py  # load M.txt and Python-literal lecture matrices
io/validation.py     # validate matrix and tour contracts
tsp/tour.py          # independent tour length calculation
```

Tour contract: a tour is a permutation of `0..n-1`; the return edge to the first city is implicit.
