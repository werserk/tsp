# Step 10 — restricted 3-opt / LK-like local search check

Дата: 2026-06-09

## Цель

Проверить, может ли ограниченный 3-opt-like local search улучшить текущий LKH upper bound без полного дорогого перебора.

Источник tour:

```txt
results/best/step6-lkh-best.json
```

## Метод

1. Берём LKH tour длины `73934`.
2. Выбираем `32` cut positions после самых длинных edges в этом tour.
3. Перебираем bounded 3-cut reconnections только на этих позициях.
4. Валидируем tour и пересчитываем длину через локальный `tour_length`.

Это не полный 3-opt и не полноценный Lin-Kernighan. Это cheap restricted check: стоит ли быстро искать локальное улучшение вокруг самых подозрительных edges.

## Команда

```bash
python experiments/step10_restricted_three_opt.py
```

Параметры:

```txt
source_artifact: results/best/step6-lkh-best.json
cut_limit: 32
max_passes: 2
candidate_cut_count: 32
```

## Результат

```txt
algorithm: restricted_three_opt_local_search
input: data/raw/matrices/M.txt
n: 1114
initial_length: 73934
length: 73934
improvement: 0
moves_applied: 0
candidates_evaluated: 34720
lower_bound: 65493.437369
absolute_gap: 8440.562631
relative_gap: 11.42%
```

Artifact:

```txt
results/runs/step10-restricted-three-opt.json
```

## Вывод

Ограниченный 3-opt-like pass не улучшил LKH tour. Это полезный negative result:

- текущий LKH tour уже локально устойчив для проверенного restricted neighborhood;
- не стоит тратить много времени на самописный partial 3-opt как главный путь;
- если усиливать upper bound, лучше запускать LKH с несколькими seeds/RUNS, а не писать слабую замену LK.

## Текущий best interval

```txt
65493.437369 <= OPT <= 73934
```

Integer-friendly form:

```txt
65494 <= OPT <= 73934
```

## Следующий шаг

Перейти к усилению LKH benchmark:

```txt
multi-seed / larger RUNS / longer MAX_TRIALS
```

и сохранять новый artifact в `results/best/` только если upper bound станет меньше `73934`.
