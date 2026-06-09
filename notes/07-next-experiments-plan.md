# Step 6+ — next experiments plan

Дата: 2026-06-09

## Текущий baseline

```txt
lower_bound: 65493.437369
upper_bound: 73934
interval: 65493.437369 <= OPT <= 73934
integer interval: 65494 <= OPT <= 73934
absolute_gap: 8440.562631
relative_gap: 11.42%
```

Artifacts:

```txt
upper: results/best/step6-lkh-best.json
lower: results/best/step9-held-karp-one-tree.json
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

### 4. Held-Karp-style 1-tree penalties — выполнено

Результат: `65493.437369`, artifact `results/best/step9-held-karp-one-tree.json`, заметка `notes/11-step9-held-karp-one-tree.md`.

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

### 5. 3-opt / restricted LK-like local search — выполнено

Результат: bounded check поверх LKH tour не улучшил `73934`; artifact `results/runs/step10-restricted-three-opt.json`, заметка `notes/12-step10-restricted-three-opt.md`.

Цель: приблизиться к Lin-Kernighan своей реализацией.

Почему не раньше:

- сложнее кода много;
- выше риск ошибок;
- LKH, вероятно, всё равно даст лучше.

### 6. LKH multi-seed upper-bound search — выполнено

Результат: первая дешёвая волна `seeds=1-20`, `RUNS=1` не улучшила `73934`; artifact `results/runs/step11-lkh-multiseed.json`, заметка `notes/13-step11-lkh-multiseed.md`.

Вывод: простая смена seed уже не даёт лёгкого upper-bound gain. Следующий upper-bound шаг должен быть более тяжёлой LKH tuning wave, а не ещё одним идентичным seed sweep.

### 7. Bounded LKH portfolio runner — infrastructure ready

Результат: реализован `experiments/step12_lkh_portfolio.py` с ETA, JSONL progress ledger, resume/force, time budget, job timeout, calibration, Markdown/HTML reports. Smoke run `A_default_r3 × seed=1` подтвердил pipeline и не улучшил `73934`; artifacts `results/runs/step12-lkh-portfolio.*`, заметка `notes/14-step12-lkh-portfolio.md`.

Следующий quality-first запуск: bounded portfolio wave `--seeds 1-20 --time-budget-hours 2 --job-timeout-minutes 20 --force`.

## Рекомендованный порядок

```txt
1. LKH benchmark — выполнено
2. Several-root 1-tree lower bound — выполнено
3. Multi-start NN → 2-opt — выполнено
4. Held-Karp 1-tree penalties — выполнено
5. 3-opt / LK-like local search — выполнено, no improvement
6. LKH multi-seed search — выполнено, no improvement
7. Bounded LKH portfolio runner — infrastructure ready
8. Next: run 1-2h quality-first portfolio wave
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
