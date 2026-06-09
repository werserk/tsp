# Step 8 — multi-start NN → 2-opt upper-bound check

Дата: 2026-06-09

## Цель

Проверить собственный объяснимый upper-bound pipeline без внешнего solver:

```txt
candidate starts → nearest-neighbor ranking → 2-opt on top starts → validate → save artifact
```

Это backup к LKH: метод проще объяснить у доски, но ожидаемо слабее SOTA.

## Команда

```bash
python experiments/step8_multistart_two_opt.py --top-ranked-starts 4
```

Параметры:

```txt
input: data/raw/matrices/M.txt
n: 1114
candidate_start_stride: 16
candidate_start_count: 71
top_ranked_starts: 4
```

Сначала все stride-16 кандидаты ранжируются по nearest-neighbor длине, затем 2-opt применяется только к четырём лучшим NN-starts. Полный запуск `1114` стартов текущей реализацией слишком дорог: один 2-opt старт занял около 57 секунд.

## Результат

```txt
algorithm: multistart_nearest_neighbor_two_opt
best_start_city: 816
best_initial_length: 89409
best_length: 77771
starts_checked: 4
total_two_opt_moves: 1226
```

Artifact:

```txt
results/best/step8-multistart-two-opt.json
```

## Сравнение с текущими bounds

```txt
lower_bound: 63494
current best upper_bound: 73934  # LKH
step8 own upper_bound: 77771
```

Step 8 не улучшил текущий global upper bound:

```txt
77771 - 73934 = 3837 worse than LKH
```

Но он улучшил наш старый single-start 2-opt baseline:

```txt
80585 - 77771 = 2814 improvement
```

## Проверка

- Tour валидируется через `validate_tour`.
- Длина пересчитывается независимо через `tour_length(..., validate=True)`.
- Artifact сохраняет command, input file, tour, lower bound, previous upper bound, gap и параметры отбора starts.

## Вывод

Собственный `NN → 2-opt` полезен как объяснимый backup, но не должен быть главным направлением для upper bound. LKH остаётся лучшим upper-bound источником.

Следующий приоритет: усилить LKH запуск несколькими `RUNS` / seeds или перейти к Held-Karp-style 1-tree penalties для lower bound.
