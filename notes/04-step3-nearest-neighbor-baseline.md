# Step 3 — nearest-neighbor upper-bound baseline

Дата: 2026-06-09

## Вывод

Получен первый валидный **upper bound** для challenge matrix `M.txt`:

```txt
length = 88839
algorithm = nearest_neighbor_multi_start
best_start = 219
starts_checked = 1114
```

Результат сохранён:

```txt
results/best/step3-nearest-neighbor-best.json
```

## Что запускалось

```bash
python experiments/step3_nearest_neighbor_baseline.py
```

Input:

```txt
data/raw/matrices/M.txt
n = 1114
```

Алгоритм:

1. Для каждого стартового города `0..1113` строится greedy nearest-neighbor tour.
2. На каждом шаге выбирается ближайший ещё не посещённый город.
3. Tie-breaking deterministic: при равной дистанции выбирается город с меньшим индексом.
4. Для каждого tour считается длина цикла с неявным возвратом в старт.
5. Лучший tour сохраняется как upper-bound artifact.

## Реализованные файлы

```txt
src/heuristics/__init__.py
src/heuristics/nearest_neighbor.py
experiments/step3_nearest_neighbor_baseline.py
tests/test_step3_nearest_neighbor.py
results/best/step3-nearest-neighbor-best.json
```

## API

```python
from src.heuristics.nearest_neighbor import (
    nearest_neighbor_tour,
    multi_start_nearest_neighbor,
    save_tour_result,
)
```

Single start:

```python
tour = nearest_neighbor_tour(matrix, start_city=0)
```

Multi-start:

```python
result = multi_start_nearest_neighbor(matrix, starts=range(n))
```

Result shape:

```python
TourResult(
    algorithm="nearest_neighbor_multi_start",
    tour=list[int],
    length=int,
    start_city=int,
    metadata={"starts_checked": int},
)
```

## Проверка результата

В запуске есть независимая проверка:

```python
independently_checked_length = tour_length(data.matrix, result.tour, validate=True)
```

То есть финальный tour:

- посещает все `1114` городов ровно один раз;
- использует тот же input file;
- пересчитан независимой функцией `tour_length`;
- сохранён в JSON с metadata.

Дополнительная проверка artifact:

```txt
algorithm nearest_neighbor_multi_start
n 1114
length 88839
start_city 219
tour_len 1114
unique_tour_len 1114
starts_checked 1114
```

Unit tests:

```txt
pytest -q
23 passed
```

## Практическое значение

`88839` теперь первый защищённый upper bound. Это baseline, не финальный результат.

Он нужен, чтобы:

- проверить end-to-end pipeline;
- иметь reference point для улучшений;
- сравнивать 2-opt / insertion / local search;
- на защите показать, что любой следующий upper bound валидируется тем же независимым checker-ом.

## Следующий шаг

Step 4: улучшить upper bound через local search.

Приоритетный вариант:

```txt
nearest-neighbor best tour → 2-opt first improvement / best improvement
```

Минимальная цель Step 4: получить tour length меньше `88839` и сохранить новый best artifact.
