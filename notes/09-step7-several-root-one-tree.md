# Step 7 — several-root 1-tree lower bound

Дата: 2026-06-09

## Цель

Усилить lower bound из Step 5 без смены доказательства: посчитать fixed-root 1-tree bound для нескольких корней и взять максимум.

## Метод

Для каждого candidate root `r` считаем тот же bound, что в Step 5:

```txt
LB(r) = MST(V \ {r}) + two cheapest edges incident to r
```

Затем берём:

```txt
LB = max_r LB(r)
```

В этом запуске candidate roots выбраны детерминированно:

```txt
0, 16, 32, ..., 1104, 1113
```

Всего: `71` candidate roots.

## Почему это корректный lower bound

Для любого Hamiltonian cycle и любого фиксированного root `r`:

1. У root `r` в tour ровно две incident edges.
2. Если удалить `r` и эти две incident edges, оставшиеся edges соединяют все вершины `V \ {r}` некоторым connected structure.
3. Вес MST на `V \ {r}` не больше веса этой connected structure.
4. Две cheapest incident edges у `r` не тяжелее двух incident edges tour у `r`.

Значит для любого `r`:

```txt
LB(r) <= OPT
```

Максимум нескольких корректных lower bounds тоже остаётся корректным lower bound:

```txt
max_r LB(r) <= OPT
```

Доказательство не требует triangle inequality.

## Результат

```txt
algorithm: several_root_one_tree_lower_bound
input: data/raw/matrices/M.txt
n: 1114
candidate_count: 71
best_root_city: 992
lower_bound: 63494
upper_bound: 73934
absolute_gap: 10440
relative_gap: 14.12%
```

## Improvement

Предыдущий lower bound:

```txt
62838
```

Новый lower bound:

```txt
63494
```

Улучшение:

```txt
+656
```

## Artifact

```txt
results/best/step7-several-root-one-tree.json
```

## Команда

```bash
python experiments/step7_several_root_one_tree.py
```

## Текущий interval

```txt
63494 <= OPT <= 73934
```

Gap:

```txt
absolute_gap: 10440
relative_gap: 14.12%
```

## Следующий шаг

Есть два сильных направления:

1. Запустить LKH с несколькими seeds / RUNS для попытки улучшить upper bound `73934`.
2. Перейти от sampled-roots к более сильному lower-bound методу: Held-Karp-style 1-tree penalties.
