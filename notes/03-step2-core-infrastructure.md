# Step 2 — базовая инфраструктура

Дата: 2026-06-09

## Вывод

Создано минимальное ядро для дальнейшей работы над bounds:

- загрузка матриц;
- валидация матриц;
- валидация tour;
- независимый пересчёт длины tour;
- smoke checks на реальных входных файлах.

## Реализованные файлы

```txt
src/
  __init__.py
  io/
    __init__.py
    matrix_loader.py
    validation.py
  tsp/
    __init__.py
    tour.py

tests/
  conftest.py
  test_step2_core.py

experiments/
  step2_smoke_checks.py
```

## API

### `load_matrix`

```python
from src.io.matrix_loader import load_matrix

data = load_matrix("data/raw/matrices/M.txt")
```

Возвращает `MatrixData`:

```python
MatrixData(
    matrix=list[list[int]],
    n=int,
    source_path=Path,
    format=str,
)
```

Поддержанные форматы:

- `plain_with_size` — `M.txt`;
- `python_literal` — `tsp_matrix1.txt`.

### `validate_matrix`

```python
from src.io.validation import validate_matrix

validate_matrix(matrix)
```

Проверяет:

- матрица непустая;
- матрица квадратная;
- нет отрицательных расстояний;
- диагональ нулевая;
- матрица симметричная по умолчанию.

### `validate_tour`

```python
from src.io.validation import validate_tour

validate_tour(tour, n)
```

Контракт tour:

```python
[0, 5, 2, 1]
```

означает цикл:

```txt
0 → 5 → 2 → 1 → 0
```

Стартовый город в конце не дублируется. Возврат в старт считается неявно.

### `tour_length`

```python
from src.tsp.tour import tour_length

length = tour_length(matrix, tour)
```

Сначала валидирует матрицу и tour, затем считает длину цикла с неявным возвратом в старт.

## Проверки

Unit tests:

```bash
pytest -q
```

Результат:

```txt
11 passed
```

Smoke checks:

```bash
python experiments/step2_smoke_checks.py
```

Результат:

```json
[
  {
    "file": "data/raw/matrices/M.txt",
    "format": "plain_with_size",
    "n": 1114,
    "sequential_tour_length": 2081212
  },
  {
    "file": "data/raw/matrices/tsp_matrix1.txt",
    "format": "python_literal",
    "n": 94,
    "sequential_tour_length": 276137
  }
]
```

## Практическое значение

Теперь любой будущий upper bound можно проверять независимо:

1. загрузить ту же матрицу;
2. проверить, что tour посещает все `1114` городов ровно один раз;
3. пересчитать длину;
4. сохранить результат с metadata.

Это защищает от типичных ошибок:

- неверный формат входного файла;
- off-by-one индексация;
- повтор города в tour;
- пропущенный город;
- забытый возврат в старт;
- неверно посчитанная длина.

## Следующий шаг

Step 3: получить первый upper bound.

Минимальный pipeline:

1. `nearest neighbor` из нескольких стартов;
2. проверка tour через `validate_tour`;
3. независимый пересчёт через `tour_length`;
4. сохранение результата в `results/best/`.
