# Step 11 — LKH multi-seed upper-bound search

Дата: 2026-06-09

## Цель

Проверить, улучшает ли систематический multi-seed запуск LKH текущий verified upper bound.

Текущий best upper bound перед запуском:

```txt
73934
```

Источник:

```txt
results/best/step6-lkh-best.json
```

## Метод

Запущен LKH 2.0.11 на canonical challenge matrix:

```txt
data/raw/matrices/M.txt
```

Параметры первой дешёвой волны:

```txt
seeds: 1-20
RUNS: 1
MAX_TRIALS: default / not set
TRACE_LEVEL: 1
```

Команда:

```bash
python experiments/step11_lkh_multiseed.py --seeds 1-20 --runs 1
```

Для каждого seed runner:

1. создаёт отдельный LKH parameter file;
2. запускает LKH;
3. парсит output tour;
4. независимо пересчитывает длину через project `tour_length(..., validate=True)`;
5. сохраняет solver length и verified length;
6. выбирает минимум по verified length.

## Результат

Artifact:

```txt
results/runs/step11-lkh-multiseed.json
```

Summary:

```txt
runs_completed: 20
runs_failed: 0
best_seed: 1
best_verified_length: 73934
improved_current_upper_bound: false
total_runtime_seconds: 437.468
```

Distribution of verified lengths:

```txt
73934: 14 seeds
73941: 2 seeds
74044: 2 seeds
73947: 1 seed
74046: 1 seed
```

Best run did **not** improve the current upper bound:

```txt
73934 -> 73934
improvement: 0
```

Because this is not a new best, the artifact is stored under `results/runs/`, not `results/best/`.

## Current interval remains unchanged

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

Дешёвый LKH multi-seed запуск показывает, что текущий tour length `73934` не является случайным единичным успехом: 14 из 20 seeds воспроизвели тот же verified best, но ни один seed не улучшил его.

Это neutral / negative benchmark result:

- `73934` остаётся текущим best upper bound;
- простая смена seed при `RUNS = 1` уже не даёт лёгкого улучшения;
- следующий upper-bound шаг должен быть не ещё один такой же seed sweep, а более тяжёлая LKH tuning wave.

## Recommended next step

Если хотим продолжать upper-bound направление, следующий bounded experiment:

```txt
seeds: 1-50 или 1-100
RUNS: 3-5
optional: MAX_TRIALS / MOVE_TYPE / PATCHING_C / PATCHING_A
```

Но это уже дороже. Если времени мало, лучше переключиться на подготовку финального объяснения результата и на одну аккуратную Held-Karp tuning wave для lower bound.
