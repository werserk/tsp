# Step 6 — LKH benchmark

Дата: 2026-06-09

## Вывод

LKH дал новый лучший **upper bound**:

```txt
previous upper_bound = 80585
new upper_bound = 73934
improvement = 6651
algorithm = lkh_lin_kernighan_helsgaun
```

С учётом Step 5 lower bound:

```txt
62838 <= OPT <= 73934
absolute_gap = 11096
relative_gap = 15.01%
```

Результат сохранён:

```txt
results/best/step6-lkh-best.json
```

## Что было сделано

Pipeline:

```txt
M.txt → TSPLIB FULL_MATRIX export → LKH run → parse TOUR_SECTION → validate_tour → tour_length → save artifact
```

Файлы:

```txt
src/integrations/lkh.py
experiments/step6_export_tsplib.py
experiments/step6_lkh_benchmark.py
tests/test_step6_lkh_integration.py
results/best/step6-lkh-best.json
data/processed/lkh/challenge-1114-full-matrix.tsp
data/processed/lkh/challenge-1114.par
data/processed/lkh/challenge-1114.lkh.tour
```

## LKH setup

Официальный архив:

```txt
http://webhotel4.ruc.dk/~keld/research/LKH/LKH-2.0.11.tgz
```

Локально собран в:

```txt
tools/LKH-2.0.11/LKH
```

`tools/` игнорируется git, потому что это внешний build artifact.

## Run parameters

```txt
RUNS = 10
MAX_TRIALS = 10000
SEED = 7
```

Команда:

```bash
python experiments/step6_lkh_benchmark.py
```

Важно: внешний agent command timed out after 600s, но LKH успел записать tour file:

```txt
data/processed/lkh/challenge-1114.lkh.tour
```

Этот tour был независимо распарсен и пересчитан нашим кодом.

## Проверка результата

Parsed tour:

```txt
tour_len = 1114
unique_tour_len = 1114
length = 73934
```

Независимая проверка:

```python
tour = parse_lkh_tour("data/processed/lkh/challenge-1114.lkh.tour")
validate_tour(tour, 1114)
length = tour_length(matrix, tour, validate=True)
```

LKH tour file также содержит:

```txt
COMMENT : Length = 73934
```

Наша проверка подтвердила ту же длину.

## Почему это defensible upper bound

Upper bound требует только предъявить корректный tour и его длину.

Для LKH результата:

1. tour посещает все `1114` городов ровно один раз;
2. возврат в старт учитывается `tour_length`;
3. длина пересчитана по исходной матрице `M.txt`, а не взята на веру из LKH output.

Следовательно:

```txt
OPT <= 73934
```

## Ограничения

- LKH — внешний эвристический solver, не доказательство optimum.
- Текущий run был interrupted by outer timeout, поэтому metadata помечает `timed_out = true`.
- Несмотря на timeout, tour artifact завершён и валиден как upper bound.

## Следующий шаг

1. Сделать короткий controlled LKH run с меньшими `MAX_TRIALS`, который гарантированно завершается в рамках лимита, и сравнить качество.
2. Либо перейти к several-root 1-tree для усиления lower bound.
3. Для защиты: объяснять LKH как сильную эвристику Lin-Kernighan, но опираться на наш independent verifier.
