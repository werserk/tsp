# Step 6+ — next experiments plan

Дата: 2026-06-09

## Текущий baseline

```txt
lower_bound: 63494
upper_bound: 73934
interval: 63494 <= OPT <= 73934
absolute_gap: 10440
relative_gap: 14.12%
```

Artifacts:

```txt
upper: results/best/step6-lkh-best.json
lower: results/best/step7-several-root-one-tree.json
```

## Цель

Не застревать на простых baseline methods. Проверить сильные внешние и собственные эвристики, сохраняя воспроизводимость:

```txt
run → parse result → validate_tour → tour_length → save artifact → document proof/explanation
```

## План экспериментов

### 1. LKH benchmark — выполнено

Результат: `73934`, artifact `results/best/step6-lkh-best.json`, заметка `notes/08-step6-lkh-benchmark.md`.

Цель: быстро получить сильный upper bound.

Pipeline:

```txt
M.txt → TSPLIB export → LKH run → parse tour → validate → save best
```

Почему:

- LKH / Lin-Kernighan-Helsgaun — сильный стандарт для TSP;
- есть шанс резко улучшить текущий upper bound `80585`;
- результат можно независимо проверить нашим `tour_length`.

Expected deliverables:

```txt
notes/08-step6-lkh-benchmark.md
experiments/step6_export_tsplib.py
experiments/step6_lkh_benchmark.py
results/best/step6-lkh-best.json
```

### 2. Several-root 1-tree lower bound — выполнено

Результат: `63494`, artifact `results/best/step7-several-root-one-tree.json`, заметка `notes/09-step7-several-root-one-tree.md`.

Цель: усилить lower bound `62838` без усложнения доказательства.

Pipeline:

```txt
for root_city in candidate_roots:
    one_tree_lower_bound(matrix, root_city)
choose max lower_bound
```

Почему:

- доказательство то же, что в Step 5;
- легко реализовать;
- может поднять lower bound.

### 3. Multi-start NN → 2-opt — выполнено

Результат: `77771`, artifact `results/best/step8-multistart-two-opt.json`, заметка `notes/10-step8-multistart-two-opt.md`.

Цель: усилить собственный upper bound без external solver.

Pipeline:

```txt
for start_city in range(n):
    nearest_neighbor_tour(matrix, start_city)
    improve_tour_two_opt(matrix, tour)
choose best
```

Почему:

- объясняется проще, чем LKH;
- полностью наш код;
- хороший backup, если LKH сложно поставить или объяснить.

Риск: текущая полная схема `1114` стартов слишком медленная; Step 8 использовал NN-ranking по stride-16 кандидатам и 2-opt только на top-4 starts. Метод улучшил старый собственный `80585 → 77771`, но не побил LKH `73934`.

### 4. Held-Karp-style 1-tree penalties

Цель: серьёзнее усилить lower bound.

Идея:

```txt
1-tree + node penalties + subgradient optimization
```

Почему:

- классический сильный lower-bound подход;
- математически хорошо выглядит для защиты.

Риск:

- сложнее реализовать и объяснить;
- нужен аккуратный proof note.

### 5. 3-opt / restricted LK-like local search

Цель: приблизиться к Lin-Kernighan своей реализацией.

Почему не раньше:

- сложнее кода много;
- выше риск ошибок;
- LKH, вероятно, всё равно даст лучше.

## Рекомендованный порядок

```txt
1. LKH benchmark
2. Several-root 1-tree lower bound
3. Multi-start NN → 2-opt
4. Held-Karp 1-tree penalties
5. 3-opt / LK-like local search
```

## Критерий успеха

К защите иметь:

```txt
best lower bound <= OPT <= best upper bound
```

Для каждого числа должно быть:

- artifact;
- команда запуска;
- input file;
- независимая проверка;
- короткое доказательство / объяснение;
- gap к противоположной границе.
