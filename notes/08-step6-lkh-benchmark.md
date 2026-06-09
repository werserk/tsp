# Step 6 — LKH benchmark

Дата: 2026-06-09

## Вывод

LKH 2.0.11 резко улучшил upper bound:

```txt
previous upper_bound = 80585
new upper_bound = 73934
improvement = 6651
improvement_vs_step4 = 8.25%
```

С учётом текущего lower bound:

```txt
62838 <= OPT <= 73934
absolute_gap = 11096
relative_gap = 15.01%
```

Результат сохранён:

```txt
results/best/step6-lkh-best.json
```

## Что запускалось

Prerequisite export:

```bash
python experiments/step6_export_tsplib.py
```

Benchmark:

```bash
python experiments/step6_lkh_benchmark.py
```

LKH binary:

```txt
tools/LKH-2.0.11/LKH
```

`tools/` не коммитится; локально LKH был скачан с official Keld Helsgaun LKH page и собран через `make`.

## Pipeline

```txt
M.txt
→ data/processed/challenge-full-matrix.tsp
→ LKH parameter file
→ data/processed/lkh-step6-output.tour
→ parse TSPLIB TOUR_SECTION
→ validate_tour
→ tour_length(validate=True)
→ results/best/step6-lkh-best.json
```

Важно: LKH не является источником истины для длины tour. Финальная длина `73934` пересчитана нашим независимым `tour_length` по исходной матрице.

## LKH parameters

```txt
PROBLEM_FILE = data/processed/challenge-full-matrix.tsp
OUTPUT_TOUR_FILE = data/processed/lkh-step6-output.tour
RUNS = 1
SEED = 1
TRACE_LEVEL = 1
```

TSPLIB export format:

```txt
TYPE: TSP
EDGE_WEIGHT_TYPE: EXPLICIT
EDGE_WEIGHT_FORMAT: FULL_MATRIX
DIMENSION: 1114
```

## Проверка artifact

```txt
algorithm lkh_2_0_11
n 1114
length 73934
previous_upper_bound 80585
improvement 6651
seed 1
runs 1
tour_len 1114
unique 1114
```

## Реализованные файлы

```txt
src/io/tsplib.py
experiments/step6_export_tsplib.py
experiments/step6_lkh_benchmark.py
tests/test_step6_tsplib_io.py
results/best/step6-lkh-best.json
```

Generated / ignored files:

```txt
data/processed/challenge-full-matrix.tsp
data/processed/lkh-step6.par
data/processed/lkh-step6-output.tour
tools/LKH-2.0.11/
```

## Практическое значение

LKH стал новым главным upper-bound источником:

```txt
best lower bound: 62838
best upper bound: 73934
```

Это лучше нашей собственной 2-opt траектории на `6651`.

Для защиты можно объяснять так:

1. Мы реализовали baseline и verifier сами.
2. Затем подключили стандартную сильную эвристику LKH.
3. Результат LKH не принят на веру: tour валидирован и пересчитан нашим кодом.

## Следующий шаг

Есть два сильных продолжения:

1. Запустить LKH с несколькими seeds / RUNS и сохранить лучший upper bound.
2. Усилить lower bound через several-root 1-tree или Held-Karp-style penalties.

Первое быстрее и, вероятно, даст ещё лучший upper bound.
