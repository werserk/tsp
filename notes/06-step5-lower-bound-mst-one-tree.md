# Step 5 — MST / 1-tree lower-bound baseline

Дата: 2026-06-09

## Вывод

Получен первый защищённый **lower bound** для challenge matrix `M.txt`:

```txt
lower_bound = 62838
algorithm = one_tree_lower_bound
root_city = 0
```

Текущий upper bound:

```txt
upper_bound = 80585
source = results/best/step4-two-opt-best.json
```

Gap:

```txt
absolute_gap = 17747
relative_gap = 22.02%
```

Результат сохранён:

```txt
results/best/step5-lower-bound-baseline.json
```

## Что запускалось

```bash
python experiments/step5_lower_bound_baseline.py
```

Input:

```txt
data/raw/matrices/M.txt
n = 1114
```

## Числа

```txt
mst_weight = 62810
mst_without_root_weight = 62808
root_city = 0
two_cheapest_root_edges = [(0, 521, 14), (0, 151, 16)]
lower_bound = 62808 + 14 + 16 = 62838
```

## Почему MST — корректный lower bound

Пусть `T` — любой Hamiltonian cycle для TSP.

Если удалить из `T` любое одно ребро, останется связный spanning tree/path на всех вершинах.

MST — это минимальное spanning tree, значит его вес не больше веса любого spanning tree:

```txt
weight(MST) <= weight(T without one edge) <= weight(T)
```

Следовательно для любого tour:

```txt
weight(MST) <= weight(T)
```

Значит:

```txt
weight(MST) <= OPT
```

Это корректная нижняя граница. Она не требует triangle inequality.

## Почему 1-tree — корректный lower bound

Фиксируем root vertex `r = 0`.

Для любого Hamiltonian cycle `T`:

1. У вершины `r` в tour ровно два incident edges.
2. Если удалить `r` и эти два ребра из tour, оставшиеся ребра соединяют все вершины `V \ {r}` в path, то есть в tree-like connected structure без циклов.
3. MST на `V \ {r}` не дороже этой оставшейся части tour.
4. Два cheapest edges из `r` не дороже двух incident edges из `r`, которые использует tour.

Поэтому для любого tour `T`:

```txt
MST(V \ {r}) + two_cheapest_edges(r) <= weight(T)
```

Следовательно:

```txt
one_tree_lower_bound <= OPT
```

Для нашего случая:

```txt
MST(V \ {0}) = 62808
cheapest edge from 0 = (0, 521, 14)
second cheapest edge from 0 = (0, 151, 16)
LB = 62808 + 14 + 16 = 62838
```

Значит:

```txt
OPT >= 62838
```

## Текущий interval для optimum

С учётом Step 4 upper bound:

```txt
62838 <= OPT <= 80585
```

## Реализованные файлы

```txt
src/bounds/__init__.py
src/bounds/mst.py
src/bounds/one_tree.py
experiments/step5_lower_bound_baseline.py
tests/test_step5_lower_bounds.py
results/best/step5-lower-bound-baseline.json
```

## API

MST:

```python
from src.bounds.mst import minimum_spanning_tree

mst = minimum_spanning_tree(matrix)
mst_without_root = minimum_spanning_tree(matrix, excluded_vertex=0)
```

1-tree:

```python
from src.bounds.one_tree import one_tree_lower_bound

result = one_tree_lower_bound(matrix, root_city=0)
```

Result shape:

```python
OneTreeResult(
    algorithm="one_tree_lower_bound",
    root_city=0,
    mst_without_root_weight=62808,
    root_edges=[(0, 521, 14), (0, 151, 16)],
    lower_bound=62838,
    metadata={"proof": "mst_without_root_plus_two_cheapest_root_edges"},
)
```

## Проверка

Unit tests:

```txt
pytest -q
34 passed
```

Artifact check:

```txt
algorithm one_tree_lower_bound
n 1114
root_city 0
mst_without_root_weight 62808
lower_bound 62838
upper_bound 80585
absolute_gap 17747
relative_gap 0.2202270894086989
root_edges [[0, 521, 14], [0, 151, 16]]
```

## Ограничения

- Это простой fixed-root 1-tree bound, не Held-Karp.
- Bound корректный, но может быть слабым.
- Для усиления lower bound нужно смотреть либо лучший root among several roots, либо Held-Karp/Lagrangian 1-tree.

## Следующий шаг

Есть два разумных направления:

1. Усилить upper bound: `multi-start NN → 2-opt`.
2. Усилить lower bound: попробовать 1-tree для нескольких root cities или перейти к Held-Karp 1-tree penalties.

Для 15-минутного объяснения уже есть защищённый interval:

```txt
62838 <= OPT <= 80585
```
