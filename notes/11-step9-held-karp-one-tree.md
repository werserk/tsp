# Step 9 — Held-Karp-style 1-tree penalties

Дата: 2026-06-09

## Цель

Усилить lower bound сильнее, чем fixed-root / several-root 1-tree, через Lagrangian relaxation:

```txt
1-tree + node penalties + subgradient optimization
```

## Идея метода

Для каждой вершины `i` вводим penalty `π_i` и считаем modified edge cost:

```txt
c'(i, j) = c(i, j) + π_i + π_j
```

Для fixed root строим минимальный 1-tree по modified costs:

```txt
T = MST(V \ {root}) + two cheapest modified root edges
```

После этого переводим вес обратно в lower bound для исходной задачи:

```txt
LB(π) = weight_c'(T) - 2 * sum_i π_i
```

Penalties обновляются subgradient step по degree violation:

```txt
π_i <- π_i + step_size * (degree_i(T) - 2)
```

## Почему это корректный lower bound

В любом Hamiltonian cycle каждая вершина имеет degree `2`. Поэтому для любого tour `H`:

```txt
weight_c'(H) = weight_c(H) + 2 * sum_i π_i
```

Минимальный 1-tree по modified costs не дороже modified cost любого Hamiltonian cycle, потому что tour является частным случаем 1-tree-like feasible object по degree-2 структуре:

```txt
weight_c'(T_min) <= weight_c'(H)
```

Значит:

```txt
weight_c'(T_min) - 2 * sum_i π_i <= weight_c(H)
```

Для оптимального tour это даёт:

```txt
LB(π) <= OPT
```

Максимум по нескольким penalty vectors тоже остаётся корректным lower bound:

```txt
max_k LB(π^k) <= OPT
```

Доказательство не требует triangle inequality.

## Команда

```bash
python experiments/step9_held_karp_one_tree.py
```

Параметры:

```txt
root_city: 0
iterations: 120
initial_step_size: 64.0
step_decay: 0.96
```

## Результат

```txt
algorithm: held_karp_lagrangian_one_tree_lower_bound
input: data/raw/matrices/M.txt
n: 1114
root_city: 0
iterations_run: 120
best_iteration: 119
lower_bound: 65493.437369
upper_bound: 73934
absolute_gap: 8440.562631
relative_gap: 11.42%
```

Так как все distances целые, `OPT` целый. Поэтому можно также безопасно формулировать integer lower bound:

```txt
65494 <= OPT
```

Но artifact хранит исходное fractional значение `65493.437369...`.

## Improvement

Предыдущий lower bound:

```txt
63494
```

Новый lower bound:

```txt
65493.437369
```

Улучшение:

```txt
+1999.437369
```

## Artifact

```txt
results/best/step9-held-karp-one-tree.json
```

## Текущий interval

```txt
65493.437369 <= OPT <= 73934
```

Integer-friendly form:

```txt
65494 <= OPT <= 73934
```

Gap:

```txt
absolute_gap: 8440.562631
relative_gap: 11.42%
```

## Вывод

Held-Karp-style penalties — лучший текущий lower-bound метод в проекте. Он заметно сократил gap `14.12% → 11.42%` и математически защищаем у доски.

Следующий приоритет: улучшать upper bound через более сильный LKH multi-run / multi-seed запуск.
